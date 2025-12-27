import os
import time
import requests
from bots import state

# Определение эмодзи для унифицированных уведомлений
EMOJI_START = "▶️"
EMOJI_STOP = "⏹️"
EMOJI_LIVE_ON = "🔴"
EMOJI_LIVE_OFF = "⚪"
EMOJI_STATUS = "📊"
EMOJI_BALANCE = "💰"
EMOJI_TRADES_INFO = "🔍"
EMOJI_SETTINGS = "⚙️"
EMOJI_BOT_RUNNING = "🟢"
EMOJI_BOT_STOPPED = "🔴"
EMOJI_WARNING = "⚠️"
EMOJI_ERROR = "❌"
EMOJI_SUCCESS = "✅"
EMOJI_INFO = "ℹ️"
EMOJI_TRADE_OPEN = "📈"
EMOJI_TRADE_CLOSE = "📉"
EMOJI_RISK_BLOCK = "🛑"
EMOJI_DAILY_REPORT = "📊"
EMOJI_ALERT = "🔔"

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# Проверяем, что токен и chat_id не пустые
if not TG_TOKEN:
    print("ERROR: TG_TOKEN is not set in environment variables")
if not TG_CHAT_ID:
    print("ERROR: TG_CHAT_ID is not set in environment variables")

API_URL = f"https://api.telegram.org/bot{TG_TOKEN}"

def keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "▶️ START", "callback_data": "START"},
                {"text": "⏹️ STOP", "callback_data": "STOP"}
            ],
            [
                {"text": "🔴 Включить LIVE", "callback_data": "ENABLE_LIVE"},
                {"text": "⚪ Выключить LIVE", "callback_data": "DISABLE_LIVE"}
            ],
            [
                {"text": "📊 STATUS", "callback_data": "STATUS"},
                {"text": "💰 BALANCE", "callback_data": "BALANCE"}
            ],
            [
                {"text": "🔍 TRADES INFO", "callback_data": "TRADES_INFO"},
                {"text": "⚙️ SETTINGS", "callback_data": "SETTINGS"}
            ]
        ]
    }

def send_message(text, kb=False):
    # Проверяем, что токен и chat_id установлены перед отправкой сообщения
    if not TG_TOKEN or not TG_CHAT_ID:
        print(f"WARNING: Cannot send message, TG_TOKEN or TG_CHAT_ID not set. Message would be: {text}")
        return
    
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"  # Использование Markdown для форматирования
    }
    if kb:
        payload["reply_markup"] = keyboard()

    # Уменьшаем задержку между сообщениями для более частых отчетов
    requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
    # Добавляем небольшую задержку, чтобы избежать блокировки сервером Telegram
    time.sleep(0.5)

def notify_start(message=""):
    """Отправить уведомление о запуске бота"""
    text = f"{EMOJI_ALERT} *START*\n{message}" if message else f"{EMOJI_ALERT} *БОТ ЗАПУЩЕН*"
    send_message(text, kb=False)

def notify_info(message):
    """Отправить информационное уведомление"""
    text = f"{EMOJI_INFO} *INFO*\n{message}"
    send_message(text, kb=False)

def notify_trade_open(symbol, side, price, qty, leverage="1x"):
    """Отправить уведомление о открытии сделки"""
    text = (
        f"{EMOJI_TRADE_OPEN} *FUTURES TRADE OPENED*\n"
        f"Symbol: `{symbol}`\n"
        f"Side: `{side}`\n"
        f"Price: `{price}`\n"
        f"Qty: `{qty}`\n"
        f"Leverage: `{leverage}`"
    )
    send_message(text, kb=False)

def notify_trade_close(symbol, side, price, qty, pnl, reason=""):
    """Отправить уведомление о закрытии сделки"""
    pnl_sign = "🟢" if pnl >= 0 else "🔴"
    reason_text = f"\nReason: `{reason}`" if reason else ""
    text = (
        f"{EMOJI_TRADE_CLOSE} *FUTURES TRADE CLOSED*\n"
        f"Symbol: `{symbol}`\n"
        f"Side: `{side}`\n"
        f"Price: `{price}`\n"
        f"Qty: `{qty}`\n"
        f"PnL: {pnl_sign} `{pnl:.4f} USDT`{reason_text}"
    )
    send_message(text, kb=False)

def notify_warning(message):
    """Отправить предупреждение"""
    text = f"{EMOJI_WARNING} *WARNING*\n{message}"
    send_message(text, kb=False)

def notify_error(message):
    """Отправить сообщение об ошибке"""
    text = f"{EMOJI_ERROR} *ERROR*\n{message}"
    send_message(text, kb=False)

def notify_risk_block(message):
    """Отправить сообщение о блокировке по риску"""
    text = f"{EMOJI_RISK_BLOCK} *RISK BLOCK*\n{message}"
    send_message(text, kb=False)

def notify_daily_report(report_data):
    """Отправить ежедневный отчет"""
    text = (
        f"{EMOJI_DAILY_REPORT} *DAILY REPORT*\n"
        f"Total Trades: `{report_data.get('total_trades', 0)}`\n"
        f"Wins: `{report_data.get('wins', 0)}`\n"
        f"Losses: `{report_data.get('losses', 0)}`\n"
        f"Win Rate: `{report_data.get('winrate', 0):.2f}%`\n"
        f"Total PnL: `{report_data.get('total_pnl', 0):.4f} USDT`\n"
        f"Best Trade: `{report_data.get('best_trade', 0):.4f} USDT`\n"
        f"Worst Trade: `{report_data.get('worst_trade', 0):.4f} USDT`\n"
        f"Max Drawdown: `{report_data.get('max_drawdown', 0):.4f} USDT`"
    )
    send_message(text, kb=False)


def send_periodic_report():
    """Отправляет расширенный отчет в телеграм каждые 3 минуты"""
    try:
        from bots.bybit_client import get_balance
        from bots.trade_logger import get_recent_trades
        from bots.risk_manager import get_daily_loss, get_trades_today
        from bots.daily_stats import daily_stats
        
        # Проверяем, не наступило ли новое сутки, и при необходимости сбрасываем статистику
        daily_stats.check_and_reset_if_new_day()
        
        balance = get_balance()
        trades = get_recent_trades(10)
        
        total_pnl = sum(trade.get("pnl", 0) for trade in trades)
        win_trades = sum(1 for trade in trades if trade.get("pnl", 0) > 0)
        loss_trades = sum(1 for trade in trades if trade.get("pnl", 0) <= 0)
        
        daily_loss = get_daily_loss()
        trades_today = get_trades_today()
        
        # Получаем текущую дневную статистику
        current_daily_stats = daily_stats.get_stats()
        
        report = f"{EMOJI_STATUS} *INFO*\n\n"
        report += f"{EMOJI_BALANCE} Баланс: *{balance:.4f} USDT*\n"
        report += f"{EMOJI_TRADES_INFO} Всего сделок: *{len(trades)}*\n"
        report += f"{EMOJI_SUCCESS} Прибыльных: *{win_trades}*\n"
        report += f"{EMOJI_ERROR} Убыточных: *{loss_trades}*\n"
        report += f"💸 Общий PnL: *{total_pnl:.4f} USDT*\n"
        report += f"{EMOJI_ERROR} Дневной убыток: *{daily_loss:.4f} USDT*\n"
        report += f"{EMOJI_TRADES_INFO} Сделок сегодня: *{trades_today}*\n\n"
        
        # Добавляем дневную статистику
        report += f"{EMOJI_DAILY_REPORT} ДНЕВНАЯ СТАТИСТИКА:\n"
        report += f"📊 Всего сделок: *{current_daily_stats['total_trades']}*\n"
        report += f"✅ Побед: *{current_daily_stats['wins']}*\n"
        report += f"❌ Убытков: *{current_daily_stats['losses']}*\n"
        report += f"📈 Процент прибыльных: *{current_daily_stats['winrate']:.2f}%*\n"
        report += f"💰 Общий PnL: *{current_daily_stats['total_pnl']:.4f} USDT*\n"
        report += f"🏆 Лучшая сделка: *{current_daily_stats['best_trade']:.4f} USDT*\n"
        report += f"📉 Худшая сделка: *{current_daily_stats['worst_trade']:.4f} USDT*\n"
        report += f"📉 Макс. просадка: *{current_daily_stats['max_drawdown']:.4f} USDT*\n\n"
        
        if trades:
            report += "*Последние сделки:*\n"
            for i, trade in enumerate(trades[-3:], 1):  # Показываем последние 3 сделки
                symbol = trade.get("symbol", "N/A")
                side = trade.get("side", "N/A")
                pnl = trade.get("pnl", 0)
                price = trade.get("price", "N/A")
                time_str = trade.get("time", "")[:19] if trade.get("time") else ""
                
                pnl_sign = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "🟡"
                report += f"{pnl_sign} {symbol} | {side} | {price} | PnL: {pnl:.4f} | {time_str}\n"
        
        send_message(report, kb=True)
    except Exception as e:
        print(f"Error sending periodic report: {e}")


def get_trades_info():
    from bots.trade_logger import get_recent_trades
    trades = get_recent_trades(10)  # Получаем последние 10 сделок
    
    if not trades:
        return f"{EMOJI_INFO} <i>Нет завершенных сделок для отображения.</i>"
    
    total_pnl = sum(trade.get("pnl", 0) for trade in trades)
    win_trades = sum(1 for trade in trades if trade.get("pnl", 0) > 0)
    loss_trades = sum(1 for trade in trades if trade.get("pnl", 0) <= 0)
    
    info = f"{EMOJI_TRADES_INFO} <b>СТАТИСТИКА ПО СДЕЛКАМ (последние {len(trades)})</b>:\n"
    info += f"{EMOJI_SUCCESS} Прибыльных: <b>{win_trades}</b>\n"
    info += f"{EMOJI_ERROR} Убыточных: <b>{loss_trades}</b>\n"
    info += f"{EMOJI_BALANCE} Общий PnL: <b>{total_pnl:.4f} USDT</b>\n\n"
    
    info += "<b>Последние сделки:</b>\n"
    for i, trade in enumerate(trades[-5:], 1):  # Показываем последние 5 сделок
        symbol = trade.get("symbol", "N/A")
        side = trade.get("side", "N/A")
        pnl = trade.get("pnl", 0)
        price = trade.get("price", "N/A")
        time_str = trade.get("time", "")[:19] if trade.get("time") else ""
        
        pnl_sign = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "🟡"
        info += f"{pnl_sign} {symbol} | {side} | {price} | PnL: {pnl:.4f} | {time_str}\n"
    
    return info


def get_settings_info():
    import os
    info = f"{EMOJI_SETTINGS} *TEKUWE NASTROIKI BOTA:*\n"
    info += f"📊 Rejim torgovli: *{os.getenv('MARKET_TYPE', 'spot')}*\n"
    info += f"{EMOJI_BALANCE} Risk na sdelku: *{float(os.getenv('RISK_PER_TRADE', '0.01'))*100}%*\n"
    info += f"{EMOJI_ERROR} Maks. dnevnoi ubytk: *{float(os.getenv('MAX_DAILY_LOSS', '0.05'))*100}%*\n"
    info += f"{EMOJI_TRADES_INFO} Maks. sdelok v den: *{os.getenv('MAX_TRADES_PER_DAY', '5')}*\n"
    info += f"🎯 Take Profit: *{float(os.getenv('TAKE_PROFIT', '0.006'))*100}%*\n"
    info += f"🛑 Stop Loss: *{float(os.getenv('STOP_LOSS', '0.003'))*100}%*\n"
    info += f"🔄 Taimfreim: *{os.getenv('TIMEFRAME', '1')}m*\n"
    info += f"📋 Simvoly: *{os.getenv('SYMBOLS', 'BTCUSDT,ETHUSDT,SOLUSDT')}*\n"
    
    return info

def get_balance_info():
    from bots.bybit_client import get_balance
    balance = get_balance()
    return f"{EMOJI_BALANCE} *BALANS: {balance:.2f} USDT*"


def send_balance():
    balance_info = get_balance_info()
    send_message(balance_info)

    requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)

def telegram_polling():
    offset = 0
    send_message(f"{EMOJI_INFO} Панель управления запущена")
    
    # Переменная для отслеживания времени последнего отчета
    last_report_time = time.time()
    
    # Интервал между отчетами (3 минуты)
    report_interval = 180  # 3 минуты в секундах

    # Оптимизированный цикл опроса с улучшенной обработкой и фильтрацией обновлений
    while True:
        try:
            # Получаем обновления сервера Telegram
            r = requests.get(
                f"{API_URL}/getUpdates",
                params={"timeout": 30, "offset": offset},
                timeout=35
            ).json()

            # Обрабатываем полученные обновления
            for u in r.get("result", []):
                offset = u["update_id"] + 1

                if "callback_query" in u:
                    cb = u["callback_query"]
                    data = cb.get("data")
                    cb_id = cb.get("id")

                    if data == "START":
                        state.BOT_ENABLED = True
                        send_message(f"{EMOJI_BOT_RUNNING} <b>БОТ ЗАПУЩЕН</b>")

                    elif data == "STOP":
                        state.BOT_ENABLED = False
                        send_message(f"{EMOJI_BOT_STOPPED} <b>БОТ ОСТАНОВЛЕН</b>")

                    elif data == "ENABLE_LIVE":
                        state.LIVE = True
                        send_message(f"{EMOJI_LIVE_ON} <b>LIVE РЕЖИМ ВКЛЮЧЕН</b> — бот будет отправлять реальные ордера")

                    elif data == "DISABLE_LIVE":
                        state.LIVE = False
                        send_message(f"{EMOJI_LIVE_OFF} <b>LIVE РЕЖИМ ОТКЛЮЧЕН</b> — бот в режиме симуляции/dry-run")

                    elif data == "STATUS":
                        send_message(
                            f"{EMOJI_STATUS} <b>СТАТУС</b>\n"
                            f"БОТ: <b>{'ON' if state.BOT_ENABLED else 'OFF'}</b>\n"
                            f"РЕЖИМ: <b>{state.TRADING_MODE}</b>"
                        )
                    
                    elif data == "BALANCE":
                        send_balance()
                    
                    elif data == "TRADES_INFO":
                        trades_info = get_trades_info()
                        send_message(trades_info, kb=True)
                    
                    elif data == "SETTINGS":
                        settings_info = get_settings_info()
                        send_message(settings_info, kb=True)

                    # Подтверждаем получение callback для удаления спиннера у кнопки
                    try:
                        if cb_id:
                            requests.post(f"{API_URL}/answerCallbackQuery",
                                        json={"callback_query_id": cb_id},
                                        timeout=5)
                    except Exception:
                        pass

            # Проверяем, нужно ли отправить периодический отчет
            current_time = time.time()
            if current_time - last_report_time >= report_interval:
                send_periodic_report()
                last_report_time = current_time
            
            # Проверяем, не наступил ли новый день для отправки отчета (в 23:59 UTC)
            from bots.daily_stats import daily_stats
            daily_stats.check_and_reset_if_new_day()

        except requests.exceptions.Timeout:
            # Обработка таймаута при ожидании обновлений - это нормальное поведение
            print("Telegram polling timeout, continuing...")
            continue
        except requests.exceptions.RequestException as e:
            # Обработка ошибок соединения
            print(f"Network error in telegram polling: {e}")
            time.sleep(10)  # Увеличиваем задержку при сетевых ошибках
        except Exception as e:
            # Обработка прочих ошибок
            print(f"Unexpected error in telegram polling: {e}")
            time.sleep(5)
