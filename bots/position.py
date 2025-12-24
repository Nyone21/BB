# bots/positions.py
positions = {}

def open_position(symbol, mode, qty, entry_price, side):
    positions[symbol] = {
        "mode": mode,
        "qty": qty,
        "entry": entry_price,
        "side": side
    }

def close_position(symbol):
    return positions.pop(symbol, None)

def has_position(symbol):
    return symbol in positions

def get_position(symbol):
    return positions.get(symbol)
