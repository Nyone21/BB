# bots/positions.py
import time

POSITIONS = {}


def open_position(symbol, side, price, qty, mode):
    POSITIONS[symbol] = {
        "symbol": symbol,
        "side": side,
        "entry_price": price,
        "qty": qty,
        "mode": mode,
        "opened_at": time.time()
    }
    return POSITIONS[symbol]


def close_position(symbol, price):
    pos = POSITIONS.get(symbol)
    if not pos:
        return None

    pos["exit_price"] = price
    pos["closed_at"] = time.time()
    del POSITIONS[symbol]
    return pos


def has_position(symbol):
    return symbol in POSITIONS


def get_position(symbol):
    return POSITIONS.get(symbol)
