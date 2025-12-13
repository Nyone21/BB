def place_order(session, side, qty):
    print(f" Sending {side} order, qty={qty}")

    session.place_order(
        category="linear",
        symbol="BTCUSDT",
        side=side,
        orderType="Market",
        qty=qty,
        timeInForce="GTC",
        reduceOnly=False,
        closeOnTrigger=False
    )
