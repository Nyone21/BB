import os

MAX_MOVE = float(os.getenv("MAX_CANDLE_MOVE", 0.01))

def is_high_volatility(candles):
    if not candles or len(candles) < 2:
        return False

    try:
        last = candles[-1]
        open_price = float(last[1])
        close_price = float(last[4])

        if open_price == 0:
            return False

        move = abs(close_price - open_price) / open_price
        return move > MAX_MOVE
    except:
        return False
