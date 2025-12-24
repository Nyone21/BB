import os

THRESHOLD = float(os.getenv("VOLATILITY_THRESHOLD", 0.004))

def choose_market(candles):
    if not candles or len(candles) < 10:
        return "spot"

    prices = [float(c[4]) for c in candles if float(c[4]) > 0]
    if len(prices) < 10:
        return "spot"

    high = max(prices)
    low = min(prices)

    if low == 0:
        return "spot"

    volatility = (high - low) / low

    return "futures" if volatility >= THRESHOLD else "spot"
