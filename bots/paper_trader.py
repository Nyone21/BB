balance = 10000.0
position = None
entry_price = 0.0
trade_log = []

def paper_trade(signal, price):
    global balance, position, entry_price, trade_log

    if signal == "BUY" and position is None:
        entry_price = price
        position = "LONG"
        trade_log.append(f"BUY at {price}")
        return "OPEN LONG"

    if signal == "SELL" and position == "LONG":
        pnl = price - entry_price
        balance += pnl
        trade_log.append(f"SELL at {price} | PnL: {pnl:.2f}")
        position = None
        return f"CLOSE LONG | PnL: {pnl:.2f}"

    return "NO ACTION"
