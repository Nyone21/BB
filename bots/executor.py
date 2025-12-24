from bots.bybit_client import session
from bots.trade_logger import log_trade


def execute_trade(symbol, signal, price, balance, mode):
    amount_usdt = 5

    if balance < amount_usdt:
        return None

    side = "Buy" if signal == "BUY" else "Sell"

    # ===== FUTURES (ONE-WAY MODE) =====
    if mode == "FUTURES":
        try:
            qty = round(amount_usdt * 9 / price, 3)

            session.place_order(
                category="linear",
                symbol=symbol,
                side=side,
                orderType="Market",
                qty=qty,
                timeInForce="IOC"
            )

            log_trade(symbol, signal, price, qty)

            return (
                f"✅ FUTURES TRADE\n"
                f"{symbol}\n"
                f"Side: {side}\n"
                f"Price: {price}\n"
                f"Leverage: 9x\n"
                f"Qty: {qty}"
            )

        except Exception as e:
            return f"❌ FUTURES ERROR\n{e}"

    # ===== SPOT =====
    else:
        try:
            qty = round(amount_usdt / price, 6)

            session.place_order(
                category="spot",
                symbol=symbol,
                side=side,
                orderType="Market",
                qty=qty
            )

            log_trade(symbol, signal, price, qty)

            return (
                f"✅ SPOT TRADE\n"
                f"{symbol}\n"
                f"Side: {side}\n"
                f"Price: {price}\n"
                f"Qty: {qty}"
            )

        except Exception as e:
            return f"❌ SPOT ERROR\n{e}"
