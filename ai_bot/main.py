"""
Главный модуль AI-бота с автоматизацией и AI-логикой.

AI-бот использует изолированный контекст (BotContext) для полной изоляции
от основного бота. Это позволяет запускать оба бота параллельно без конфликтов.

Особенности:
- Автоматический цикл торговли
- Периодические отчеты в Telegram каждые 3 минуты
- Интеграция AI-логики (ai_brain, ai_memory) для принятия решений
- Обучение на основе результатов сделок
"""

import os
import time
import traceback
import threading
from datetime import datetime
from bots.core.bot_context import BotContext
from bots.core.bybit_client_factory import create_bybit_session
from bots.core.data_manager import DataManager

# Импортируем функции из основного бота
from bots.analyzer import analyze_market
from bots.ai_filter import ai_filter
from bots.trader import execute_trade
from bots.telegram import send_message
from bots import learning
from bots import pnl_tracker

# Импортируем улучшенную AI-логику
from ai_bot.ai_enhanced import AIBrain, update_trade_feedback

# GitHub Actions: run once and exit
RUN_ONCE = os.getenv('RUN_ONCE', '0').lower() in ('1','true','yes')

# ================= CONFIG =================
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
ENV_TRADE_MODE = os.getenv("TRADE_MODE", "AUTO").upper()
SYMBOLS = os.getenv("SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT").split(",")
TRADE_INTERVAL = int(os.getenv("AI_BOT_TRADE_INTERVAL", "30"))  # Интервал между проверками (секунды)
REPORT_INTERVAL = 180  # Отчеты каждые 3 минуты (180 секунд)

# AI-бот использует отдельные API ключи (опционально)
AI_BOT_API_KEY = os.getenv("AI_BOT_API_KEY")  # Если не указан, используется основной
AI_BOT_API_SECRET = os.getenv("AI_BOT_API_SECRET")  # Если не указан, используется основной


def create_ai_bot_context() -> BotContext:
    """
    Создать изолированный контекст для AI-бота.
    
    Returns:
        BotContext: Изолированный контекст AI-бота
    """
    context = BotContext(
        bot_name="ai_bot",
        api_key=AI_BOT_API_KEY,
        api_secret=AI_BOT_API_SECRET,
        data_dir="data"
    )
    
    # Настраиваем из переменных окружения
    context.configure_from_env()
    
    # Переопределяем режим торговли если нужно
    if ENV_TRADE_MODE:
        context.state.set_trading_mode(ENV_TRADE_MODE)
    
    return context


# Глобальный контекст AI-бота
_ai_bot_context = None


def get_ai_bot_context() -> BotContext:
    """Получить контекст AI-бота (ленивая инициализация)."""
    global _ai_bot_context
    if _ai_bot_context is None:
        _ai_bot_context = create_ai_bot_context()
    return _ai_bot_context


def get_recent_trades(limit: int = 10):
    """Получить последние сделки из памяти AI-бота."""
    context = get_ai_bot_context()
    memory = context.data_manager.load_memory()
    # Сортируем по времени (новые первыми) и берем последние N
    sorted_trades = sorted(memory, key=lambda x: x.get("time", ""), reverse=True)
    return sorted_trades[:limit]


def send_ai_bot_periodic_report():
    """Отправляет расширенный отчет AI-бота в телеграм каждые 3 минуты."""
    try:
        context = get_ai_bot_context()
        session = context.session
        
        # Получаем баланс
        data = session.get_wallet_balance(accountType="UNIFIED")
        coins = data["result"]["list"][0]["coin"]
        balance = 0.0
        for c in coins:
            if c["coin"] == "USDT":
                balance = float(c["walletBalance"])
                break
        
        # Получаем последние сделки
        trades = get_recent_trades(10)
        
        # Статистика по сделкам
        total_pnl = sum(trade.get("pnl", 0) for trade in trades)
        win_trades = sum(1 for trade in trades if trade.get("pnl", 0) > 0)
        loss_trades = sum(1 for trade in trades if trade.get("pnl", 0) <= 0)
        
        # AI статистика
        ai_brain = AIBrain(context.data_manager)
        ai_stats = ai_brain.get_stats()
        ai_confidence = ai_stats.get("confidence", {})
        ai_wins = ai_stats.get("win_trades", 0)
        ai_losses = ai_stats.get("loss_trades", 0)
        ai_total = ai_stats.get("total_trades", 0)
        ai_winrate = ai_stats.get("winrate", 0)
        
        # Дневная статистика
        daily_stats = context.data_manager.load_daily_stats()
        
        report = "🤖 *AI BOT REPORT*\n\n"
        report += f"💰 Баланс: *{balance:.4f} USDT*\n"
        report += f"📊 Всего сделок: *{len(trades)}*\n"
        report += f"✅ Прибыльных: *{win_trades}*\n"
        report += f"❌ Убыточных: *{loss_trades}*\n"
        report += f"💸 Общий PnL: *{total_pnl:.4f} USDT*\n\n"
        
        # AI статистика
        report += "🧠 *AI СТАТИСТИКА:*\n"
        report += f"Всего сделок AI: *{ai_total}*\n"
        report += f"Побед: *{ai_wins}*\n"
        report += f"Поражений: *{ai_losses}*\n"
        report += f"Win Rate: *{ai_winrate:.2f}%*\n"
        report += f"Уверенность BUY: *{ai_confidence.get('BUY', 1.0):.2f}*\n"
        report += f"Уверенность SELL: *{ai_confidence.get('SELL', 1.0):.2f}*\n\n"
        
        # Дневная статистика
        if daily_stats.get("total_trades", 0) > 0:
            report += "📅 *ДНЕВНАЯ СТАТИСТИКА:*\n"
            report += f"Всего сделок: *{daily_stats.get('total_trades', 0)}*\n"
            report += f"Побед: *{daily_stats.get('wins', 0)}*\n"
            report += f"Убытков: *{daily_stats.get('losses', 0)}*\n"
            report += f"Win Rate: *{daily_stats.get('winrate', 0):.2f}%*\n"
            report += f"Общий PnL: *{daily_stats.get('total_pnl', 0):.4f} USDT*\n"
            report += f"Лучшая сделка: *{daily_stats.get('best_trade', 0):.4f} USDT*\n"
            report += f"Худшая сделка: *{daily_stats.get('worst_trade', 0):.4f} USDT*\n\n"
        
        # Последние сделки
        if trades:
            report += "*Последние сделки:*\n"
            for trade in trades[-5:]:  # Последние 5 сделок
                symbol = trade.get("symbol", "N/A")
                side = trade.get("side", "N/A")
                pnl = trade.get("pnl", 0)
                price = trade.get("price", "N/A")
                time_str = trade.get("time", "")[:19] if trade.get("time") else ""
                
                pnl_sign = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "🟡"
                report += f"{pnl_sign} {symbol} | {side} | {price} | PnL: {pnl:.4f} | {time_str}\n"
        
        send_message(report)
    except Exception as e:
        print(f"Error sending AI bot periodic report: {e}")
        traceback.print_exc()


def trading_cycle(context: BotContext):
    """
    Основной цикл торговли AI-бота.
    """
    try:
        session = context.session
        
        # Получаем баланс
        data = session.get_wallet_balance(accountType="UNIFIED")
        coins = data["result"]["list"][0]["coin"]
        balance = 0.0
        for c in coins:
            if c["coin"] == "USDT":
                balance = float(c["walletBalance"])
                break
        
        context.state.update_balance(balance)
        
        market_type = os.getenv("MARKET_TYPE", "spot").upper()
        
        for symbol in SYMBOLS:
            if not context.state.bot_enabled:
                continue
            
            try:
                # Получаем данные рынка
                ticker_data = session.get_tickers(category="spot", symbol=symbol)
                price = float(ticker_data["result"]["list"][0]["lastPrice"])
                
                kline_data = session.get_kline(
                    category="spot",
                    symbol=symbol,
                    interval="5",
                    limit=50
                )
                candles = kline_data["result"]["list"]
                
                # Анализ рынка
                raw, ema, closes, highs, lows = analyze_market(candles)
                
                # AI фильтр
                ai_signal = ai_filter(raw, price, ema, closes, symbol, highs, lows)
                
                # AI решение с учетом обучения (используем улучшенный AI-мозг)
                ai_brain = AIBrain(context.data_manager)
                final_signal = ai_brain.decide(raw, ai_signal)
                
                # Обновляем статистику обучения
                try:
                    learning.update_stats()
                except Exception:
                    pass
                
                # Проверяем возможность торговли
                from bots.decision import can_trade
                can_trade_result, reason = can_trade(candles)
                
                # Проверяем кулдаун
                if not context.state.get_trade_cooldown(symbol, 60):  # 60 секунд кулдаун
                    continue
                
                # Выполняем сделку если есть сигнал
                if final_signal in ("BUY", "SELL") and can_trade_result:
                    result = execute_trade(
                        symbol=symbol,
                        signal=final_signal,
                        price=price,
                        balance=balance,
                        mode=market_type,
                        dry_run=DRY_RUN,
                    )
                    if result:
                        send_message(f"🤖 AI BOT: {result}")
                        context.state.record_trade(symbol)
                        
                        # Сохраняем сделку через DataManager
                        trade_data = {
                            "symbol": symbol,
                            "side": final_signal,
                            "price": price,
                            "time": datetime.utcnow().isoformat(),
                            "pnl": 0.0,  # Будет обновлено позже
                            "ai_signal": ai_signal,
                            "raw_signal": raw
                        }
                        context.data_manager.append_trade(trade_data)
                        
                        # Обновляем обратную связь для AI (будет обновлено когда PnL будет известен)
                        # Это произойдет позже через pnl_tracker
                        
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
        
        # Проверяем PnL и обновляем AI обратную связь
        try:
            pnl_tracker.check_balance_and_record()
            
            # Обновляем обратную связь для AI на основе завершенных сделок
            recent_trades = get_recent_trades(5)
            for trade in recent_trades:
                pnl = trade.get("pnl", 0.0)
                if pnl != 0.0:  # Если PnL уже известен
                    update_trade_feedback(context.data_manager, trade)
        except Exception as e:
            print(f"Error updating PnL and AI feedback: {e}")
            
    except Exception as e:
        print(f"Error in trading cycle: {e}")
        traceback.print_exc()


def single_run():
    """
    Однократный запуск AI-бота для GitHub Actions.
    """
    context = get_ai_bot_context()
    
    run_id = os.getenv("GITHUB_RUN_ID", "Unknown")
    
    heartbeat_msg = (
        f"✅ AI BOT RUN START\n"
        f"Date/Time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Workflow Run ID: {run_id}\n"
        f"Symbols: {', '.join(SYMBOLS)}\n"
        f"BOT_ENABLED: {context.state.bot_enabled}\n"
        f"DRY_RUN: {DRY_RUN}\n"
        f"LIVE: {context.state.live}\n"
        f"TRADING_MODE: {context.state.trading_mode}"
    )
    send_message(heartbeat_msg)
    
    trading_cycle(context)
    
    end_msg = f"✅ AI BOT RUN END"
    send_message(end_msg)


def start():
    """
    Запуск AI-бота с автоматическим циклом и периодическими отчетами.
    """
    context = get_ai_bot_context()
    
    start_mode = "DRY-RUN" if DRY_RUN else "LIVE"
    send_message(f"🤖 AI BOT STARTED ({start_mode}) MODE={context.state.trading_mode}")
    send_message(f"📊 Отчеты будут отправляться каждые {REPORT_INTERVAL // 60} минут")
    
    # Переменная для отслеживания времени последнего отчета
    last_report_time = time.time()
    
    # Если RUN_ONCE, выполняем один раз и выходим
    if RUN_ONCE:
        single_run()
        return
    
    # Основной цикл
    try:
        while True:
            if context.state.bot_enabled:
                trading_cycle(context)
            
            # Проверяем, нужно ли отправить периодический отчет
            current_time = time.time()
            if current_time - last_report_time >= REPORT_INTERVAL:
                send_ai_bot_periodic_report()
                last_report_time = current_time
            
            # Ждем перед следующей итерацией
            time.sleep(TRADE_INTERVAL)
            
    except KeyboardInterrupt:
        send_message("🤖 AI BOT STOPPED by user")
    except Exception as e:
        err = traceback.format_exc()
        print(err)
        send_message(f"🤖 AI BOT ERROR:\n{err}")


if __name__ == "__main__":
    start()

