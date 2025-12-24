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

# ================= CONFIG =================
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
ENV_TRADE_MODE = os.getenv("TRADE_MODE", "AUTO").upper()
SYMBOLS = os.getenv("SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT").split(",")
TRADE_REPORT_INTERVAL = int(os.getenv("TRADE_REPORT_INTERVAL", "240"))
# ==========================================

state.TRADING_MODE = ENV_TRADE_MODE
state.LIVE = not DRY_RUN

start_mode = "DRY-RUN" if DRY_RUN else "LIVE"
send_message(f" AI BOT STARTED ({start_mode})  MODE={state.TRADING_MODE}")

def main_loop():
    last_report = 0

    while True:
        try:
            if not state.BOT_ENABLED:
                time.sleep(5)
                continue

            balance = get_balance()
            now = time.time()

            for symbol in SYMBOLS:
                price = get_price(symbol)
                candles = get_candles(symbol)

                raw, ema, closes = analyze_market(candles)
                ai = ai_filter(raw, price, ema, closes, symbol)

                try:
                    learning.update_stats()
                except Exception:
                    pass

                market_type = os.getenv("MARKET_TYPE", "spot").upper()

                if ai in ("BUY", "SELL"):
                    from bots.decision import can_trade
                    can_trade_result, reason = can_trade(candles)

                    if can_trade_result:
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
                    else:
                        if reason in ("LOW_BALANCE", "FLAT_MARKET"):
                            send_message(f" {symbol}: {reason}")

            try:
                pnl_tracker.check_balance_and_record()
            except Exception:
                pass

            if now - last_report >= TRADE_REPORT_INTERVAL:
                trades = trade_logger.get_trades_since(last_report)
                total_pnl = sum(t.get("pnl", 0) for t in trades)

                lines = [
                    f" TRADE REPORT ({TRADE_REPORT_INTERVAL}s)",
                    f"Trades: {len(trades)}",
                    f"PnL: {total_pnl:.4f}",
                ]

                for t in trades[-10:]:
                    lines.append(
                        f"- {t.get('symbol')} {t.get('side')} price={t.get('price')} qty={t.get('qty')}"
                    )

                send_message("\n".join(lines))
                last_report = now

            time.sleep(20)

        except Exception:
            err = traceback.format_exc()
            print(err)
            send_message(f" ERROR:\n{err}")
            time.sleep(10)

def start():
    tg = threading.Thread(target=telegram_polling, daemon=True)
    tg.start()
    main_loop()

if __name__ == "__main__":
    start()
