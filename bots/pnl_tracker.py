import os
import time
import logging
from bots.bybit_client import get_balance
from bots import trade_logger, state
from bots.bybit_client import get_positions
from bots.telegram import notify_trade_close
from bots.daily_stats import daily_stats

logger = logging.getLogger(__name__)

BALANCE_DELTA_THRESHOLD = float(os.getenv("BALANCE_DELTA_THRESHOLD", "0.001"))


def check_balance_and_record():
    """Check wallet balance, detect changes and attach PnL to last trade if detected.

    Should be called periodically from main loop after fetching balance.
    """
    try:
        bal = get_balance()
    except Exception as e:
        logger.exception("Failed to fetch balance for PnL tracker")
        return

    last = getattr(state, "last_balance", None)
    if last is None:
        state.last_balance = bal
        return

    delta = bal - last
    if abs(delta) >= BALANCE_DELTA_THRESHOLD:
        # try to attach to last trade (balance-delta fallback)
        ok = False
        try:
            ok = trade_logger.attach_pnl_to_last_trade(delta)
        except Exception:
            logger.exception("attach_pnl failed")
            ok = False

        msg = (
            f"📈 Обнаружено изменение баланса: {delta:.6f} USDT\n"
            f"Прикреплено к последней сделке: {ok}"
        )
        try:
            # Отправляем уведомление через новый формат
            from bots.telegram import send_message
            send_message(msg)
        except Exception:
            logger.exception("Failed to send PnL update message")
        
        # Проверяем риски после обновления PnL
        try:
            from bots.risk_manager import check_daily_limits
            check_daily_limits(bal)
        except Exception:
            logger.exception("Failed to check daily limits after PnL update")

    # additionally, try to read positions via API and attach realized PnL from closed positions
    try:
        positions = get_positions(category="linear")
        for p in positions:
            # if position is closed but has realizedPnl field, attach it
            realized = p.get("realisedPnl") or p.get("realizedPnl") or 0
            symbol = p.get("symbol")
            size = p.get("size") or p.get("qty")
            if realized and float(realized) != 0:
                # attach to last trade for this symbol
                attached = trade_logger.attach_pnl_to_last_trade(float(realized))
                if attached:
                    # Отправляем уведомление о закрытии сделки с PnL
                    notify_trade_close(symbol, "CLOSE", 0, size, float(realized), "realized from position")
                    # Обновляем дневную статистику
                    daily_stats.update_stats(float(realized))
    except Exception:
        logger.debug("Positions check failed or not supported by API")

    state.last_balance = bal