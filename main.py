import os
import time
import traceback
import threading

from bots.bybit_client import get_balance, get_price, get_candles
from bots import trade_logger
from bots.analyzer import analyze_market
from bots.ai_filter import ai_filter
from bots import learning
from bots import pnl_tracker
from bots.trader import execute_trade
from bots.telegram import send_message, telegram_polling
from bots import state

# GitHub Actions: run once and exit
RUN_ONCE = os.getenv('RUN_ONCE', '0').lower() in ('1','true','yes')


# ================= CONFIG =================
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
ENV_TRADE_MODE = os.getenv("TRADE_MODE", "AUTO").upper()
SYMBOLS = os.getenv("SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT").split(",")
TRADE_REPORT_INTERVAL = int(os.getenv("TRADE_REPORT_INTERVAL", "60"))  # Уменьшено до 1 минуты для более частых отчетов
# ==========================================

state.TRADING_MODE = ENV_TRADE_MODE
state.LIVE = not DRY_RUN

start_mode = "DRY-RUN" if DRY_RUN else "LIVE"
send_message(f" AI BOT STARTED ({start_mode})  MODE={state.TRADING_MODE}")

def single_run():
    """
    Однократный запуск бота для GitHub Actions
    """
    import os
    from datetime import datetime
    
    # Получаем номер запуска из переменной окружения GitHub Actions
    run_id = os.getenv("GITHUB_RUN_ID", "Unknown")
    
    # Отправляем heartbeat сообщение в начале запуска
    heartbeat_msg = (
        f"✅ RUN START\n"
        f"Date/Time (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Workflow Run ID: {run_id}\n"
        f"Symbols: {', '.join(SYMBOLS)}\n"
        f"BOT_ENABLED: {state.BOT_ENABLED}\n"
        f"DRY_RUN: {DRY_RUN}\n"
        f"LIVE: {state.LIVE}\n"
        f"TRADING_MODE: {state.TRADING_MODE}"
    )
    send_message(heartbeat_msg)
    
    try:
        # Убедимся, что бот включен
        # Теперь состояние зависит от переменных окружения, а не устанавливается в True
        state.BOT_ENABLED = os.getenv("BOT_ENABLED", "True").lower() in ("1", "true", "yes")
        state.LIVE = not DRY_RUN  # LIVE режим включается когда не DRY_RUN
        
        balance = get_balance()
        now = time.time()

        # Счетчики для итогового отчета
        processed_symbols = 0
        buy_signals = 0
        sell_signals = 0
        executed_trades = 0
        
        symbol_logs = []

        for symbol in SYMBOLS:
            price = get_price(symbol)
            candles = get_candles(symbol)

            raw, ema, closes, highs, lows = analyze_market(candles)
            ai = ai_filter(raw, price, ema, closes, symbol, highs, lows)

            try:
                learning.update_stats()
            except Exception:
                pass

            market_type = os.getenv("MARKET_TYPE", "spot").upper()

            # Проверяем возможность торговли
            from bots.decision import can_trade
            can_trade_result, reason = can_trade(candles)
            
            # Логируем результаты анализа для каждого символа
            symbol_log = f"{symbol} price={price:.4f} ai={ai} can_trade={can_trade_result} reason={reason}"
            symbol_logs.append(symbol_log)

            if ai in ("BUY", "SELL"):
                if ai == "BUY":
                    buy_signals += 1
                elif ai == "SELL":
                    sell_signals += 1
                
                if can_trade_result and state.BOT_ENABLED:
                    result = execute_trade(
                        symbol=symbol,
                        signal=ai,
                        price=price,
                        balance=balance,
                        mode=market_type,
                        dry_run=DRY_RUN,
                    )
                    if result:
                        send_message(result)
                        executed_trades += 1
                else:
                    if reason in ("LOW_BALANCE", "FLAT_MARKET"):
                        send_message(f" {symbol}: {reason}")

            processed_symbols += 1

        # Отправляем логи по каждому символу
        if symbol_logs:
            log_message = "📈 Symbol Analysis Logs:\n" + "\n".join(symbol_logs)
            send_message(log_message)

        try:
            pnl_tracker.check_balance_and_record()
        except Exception:
            pass

        # Отправляем итоговое сообщение
        end_msg = (
            f"✅ RUN END\n"
            f"Processed symbols: {processed_symbols}\n"
            f"BUY signals: {buy_signals}\n"
            f"SELL signals: {sell_signals}\n"
            f"Executed trades: {executed_trades}"
        )
        send_message(end_msg)

    except Exception:
        err = traceback.format_exc()
        print(err)
        send_message(f" ERROR:\n{err}")


def start():
    """
    Запуск бота для GitHub Actions
    """
    # В режиме GitHub Actions не запускаем телеграм-опрос
    single_run()

if __name__ == "__main__":
    start()
