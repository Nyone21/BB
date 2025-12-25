from typing import Any
import logging
import os
import time
from datetime import datetime

from bots.bybit_client import session, place_futures_order, place_spot_order
from bots.telegram import send_message
from bots import trade_logger
from bots import state
from bots import risk_manager

USDT_PER_TRADE = 5.0
MIN_QTY = 1

DRY_RUN = os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes")

logger = logging.getLogger(__name__)


def execute_trade(symbol: str, signal: str, price: float, balance: float, mode: str, dry_run: bool | None = None) -> str:
    """Execute a market trade for `FUTURES` or `SPOT` and return status text.

    This function normalizes inputs, performs a minimal validation and
    delegates order placement to `session.place_order` from `bybit_client`.
    On error it reports via `send_message` and the logger.
    """
    mode = (mode or "").upper()
    signal = (signal or "").upper()
    if dry_run is None:
        # runtime live flag overrides env DRY_RUN
        dry_run = DRY_RUN and not getattr(__import__('bots.state', fromlist=['state']).LIVE, False)

    try:
        # risk check: disallow trade if risk manager blocks it (only for live orders)
        try:
            allow, reason = risk_manager.allow_trade(balance)
        except Exception:
            allow, reason = True, "ok"
        if not allow and not dry_run:
            return f"⚠️ ТОРГОВЛЯ ОТКЛОНЕНА: {reason}"

        if mode == "FUTURES":
            qty = max(MIN_QTY, 1)
            side = "Buy" if signal == "BUY" else "Sell"
            leverage = int(os.getenv("FUTURES_LEVERAGE", "1"))

            if dry_run:
                logger.info("DRY RUN - skipping FUTURES order placement")
                # record simulated futures trade
                trade_sim = {
                    "symbol": symbol,
                    "side": side,
                    "price": price,
                    "qty": qty,
                    "simulated": True,
                    "time": datetime.utcnow().isoformat(),
                    "pnl": 0.0,
                }
                try:
                    trade_logger.save_trade(trade_sim)
                except Exception:
                    logger.exception("Failed to save simulated futures trade")
                state.OPEN_TRADES[symbol] = time.time()
                try:
                    risk_manager.record_trade_result(trade_sim.get("pnl", 0.0))
                except Exception:
                    pass
                return (
                    f"[DRY RUN] ✅ FUTURES TRADE (SIMULATED)\n"
                    f"{symbol}\n"
                    f"Side: {side}\n"
                    f"Qty: {qty}"
                )

            resp = place_futures_order(symbol, side, qty, leverage)

            # record trade
            trade = {
                "symbol": symbol,
                "side": side,
                "price": price,
                "qty": qty,
                "resp": repr(resp),
                "simulated": False,
                "time": datetime.utcnow().isoformat(),
                "pnl": 0.0,
            }
            try:
                trade_logger.save_trade(trade)
            except Exception:
                logger.exception("Failed to save trade")
            state.OPEN_TRADES[symbol] = time.time()
            try:
                risk_manager.record_trade_result(trade.get("pnl", 0.0))
            except Exception:
                pass

            return (
                f"✅ FUTURES TRADE EXECUTED\n"
                f"{symbol}\n"
                f"Side: {side}\n"
                f"Qty: {qty}\n"
                f"Resp: {repr(resp)}"
            )

        elif mode == "SPOT":
            if price <= 0:
                raise ValueError("Price must be positive for SPOT orders")

            # Используем риск-менеджмент для определения размера позиции
            from bots.risk_manager import compute_trade_amount
            from bots.bybit_client import get_balance
            balance = get_balance()
            trade_amount = compute_trade_amount(balance)
            
            qty = trade_amount / price
            qty_rounded = round(qty, 6)
            if qty_rounded <= 0:
                raise ValueError("Calculated quantity is zero or too small")

            if dry_run:
                logger.info("DRY RUN - skipping SPOT order placement")
                # record simulated trade
                trade = {
                    "symbol": symbol,
                    "side": signal,
                    "price": price,
                    "qty": qty_rounded,
                    "simulated": True,
                    "time": datetime.utcnow().isoformat(),
                    "pnl": 0.0,
                }
                try:
                    trade_logger.save_trade(trade)
                except Exception:
                    logger.exception("Failed to save simulated trade")
                state.OPEN_TRADES[symbol] = time.time()
                try:
                    risk_manager.record_trade_result(trade.get("pnl", 0.0))
                except Exception:
                    pass
                return (
                    f"[DRY RUN] ✅ SPOT TRADE (SIMULATED)\n"
                    f"{symbol}\n"
                    f"Side: {signal}\n"
                    f"USDT: {trade_amount}\n"
                    f"Qty: {qty_rounded}"
                )

            resp = place_spot_order(symbol, signal, trade_amount)

            trade = {
                "symbol": symbol,
                "side": signal,
                "price": price,
                "qty": qty_rounded,
                "resp": repr(resp),
                "simulated": False,
                "time": datetime.utcnow().isoformat(),
                "pnl": 0.0,
            }
            try:
                trade_logger.save_trade(trade)
            except Exception:
                logger.exception("Failed to save trade")
            state.OPEN_TRADES[symbol] = time.time()
            try:
                risk_manager.record_trade_result(trade.get("pnl", 0.0))
            except Exception:
                pass

            return (
                f"✅ SPOT TRADE\n"
                f"{symbol}\n"
                f"Side: {signal}\n"
                f"USDT: {trade_amount}\n"
                f"Qty: {qty_rounded}\n"
                f"Resp: {repr(resp)}"
            )

        else:
            return f"⚠️ UNKNOWN MODE: {mode}"

    except Exception as e:
        err = f"❌ ОШИБКА ({mode})\n{e}"
        try:
            send_message(err)
        except Exception:
            logger.exception("Failed to send error message")
        logger.exception("Trade execution failed")
        return err
