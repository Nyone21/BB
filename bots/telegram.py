import os
import time
import requests
from bots import state

# Определение эмодзи для использования в сообщениях
EMOJI_START = "▶️"
EMOJI_STOP = "⛔"
EMOJI_LIVE_ON = "🔴"
EMOJI_LIVE_OFF = "⚪"
EMOJI_STATUS = "📊"
EMOJI_BALANCE = "💰"
EMOJI_TRADES_INFO = "🔍"
EMOJI_SETTINGS = "⚙️"
EMOJI_BOT_RUNNING = "🟢"
EMOJI_BOT_STOPPED = "🚫"
EMOJI_WARNING = "⚠️"
EMOJI_ERROR = "❌"
EMOJI_SUCCESS = "✅"
EMOJI_INFO = "ℹ️"

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
API_URL = f"https://api.telegram.org/bot{TG_TOKEN}"

def keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "▶️ START", "callback_data": "START"},
                {"text": "⛔ STOP", "callback_data": "STOP"}
            ],
            [
                {"text": "🔴 Включить LIVE", "callback_data": "ENABLE_LIVE"},
                {"text": "⚪ Выключить LIVE", "callback_data": "DISABLE_LIVE"}
            ],
            [
                {"text": "📊 STATUS", "callback_data": "STATUS"},
                {"text": "📈 BALANCE", "callback_data": "BALANCE"}
            ],
            [
                {"text": "🔍 TRADES INFO", "callback_data": "TRADES_INFO"},
                {"text": "⚙️ SETTINGS", "callback_data": "SETTINGS"}
            ]
        ]
    }

def send_message(text, kb=True):
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"  # Использование HTML для форматирования
    }
    if kb:
        payload["reply_markup"] = keyboard()

    requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)


def send_periodic_report():
    """Отправляет расширенный отчет в телеграм каждые 3 минуты"""
    try:
        from bots.bybit_client import get_balance
        from bots.trade_logger import get_recent_trades
        from bots.risk_manager import get_daily_loss, get_trades_today
        
        balance = get_balance()
        trades = get_recent_trades(10)
        
        total_pnl = sum(trade.get("pnl", 0) for trade in trades)
        win_trades = sum(1 for trade in trades if trade.get("pnl", 0) > 0)
        loss_trades = sum(1 for trade in trades if trade.get("pnl", 0) <= 0)
        
        daily_loss = get_daily_loss()
        trades_today = get_trades_today()
        
        report = f"{EMOJI_STATUS} <b>РАСШИРЕННЫЙ ОТЧЕТ О БОТЕ (3 мин)</b>\n\n"
        report += f"{EMOJI_BALANCE} Баланс: <b>{balance:.4f} USDT</b>\n"
        report += f"{EMOJI_TRADES_INFO} Всего сделок: <b>{len(trades)}</b>\n"
        report += f"{EMOJI_SUCCESS} Прибыльных: <b>{win_trades}</b>\n"
        report += f"{EMOJI_ERROR} Убыточных: <b>{loss_trades}</b>\n"
        report += f"💸 Общий PnL: <b>{total_pnl:.4f} USDT</b>\n"
        report += f"{EMOJI_ERROR} Дневной убыток: <b>{daily_loss:.4f} USDT</b>\n"
        report += f"{EMOJI_TRADES_INFO} Сделок сегодня: <b>{trades_today}</b>\n\n"
        
        if trades:
            report += "<b>Последние сделки:</b>\n"
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
    info = f"{EMOJI_SETTINGS} <b>ТЕКУЩИЕ НАСТРОЙКИ БОТА:</b>\n"
    info += f"📊 Режим торговли: <b>{os.getenv('MARKET_TYPE', 'spot')}</b>\n"
    info += f"{EMOJI_BALANCE} Риск на сделку: <b>{float(os.getenv('RISK_PER_TRADE', '0.01'))*100}%</b>\n"
    info += f"{EMOJI_ERROR} Макс. дневной убыток: <b>{float(os.getenv('MAX_DAILY_LOSS', '0.05'))*100}%</b>\n"
    info += f"{EMOJI_TRADES_INFO} Макс. сделок в день: <b>{os.getenv('MAX_TRADES_PER_DAY', '5')}</b>\n"
    info += f"🎯 Take Profit: <b>{float(os.getenv('TAKE_PROFIT', '0.006'))*100}%</b>\n"
    info += f"🛑 Stop Loss: <b>{float(os.getenv('STOP_LOSS', '0.003'))*100}%</b>\n"
    info += f"🔄 Таймфрейм: <b>{os.getenv('TIMEFRAME', '1')}m</b>\n"
    info += f"📋 Символы: <b>{os.getenv('SYMBOLS', 'BTCUSDT,ETHUSDT,SOLUSDT')}</b>\n"
    
    return info

def get_balance_info():
    from bots.bybit_client import get_balance
    balance = get_balance()
    return f"{EMOJI_BALANCE} БАЛАНС: <b>{balance:.2f} USDT</b>"


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
