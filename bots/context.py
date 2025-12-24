def market_context(closes):
    if len(closes) < 50:
        return {
            "trend": "UNKNOWN",
            "volatility": "LOW",
            "night": False
        }

    # ===== ТРЕНД =====
    sma_short = sum(closes[-10:]) / 10
    sma_long = sum(closes[-50:]) / 50

    if sma_short > sma_long * 1.002:
        trend = "UP"
    elif sma_short < sma_long * 0.998:
        trend = "DOWN"
    else:
        trend = "FLAT"

    # ===== ВОЛАТИЛЬНОСТЬ =====
    diffs = []
    for i in range(1, len(closes)):
        diffs.append(abs(closes[i] - closes[i - 1]))

    avg_move = sum(diffs[-20:]) / 20
    price = closes[-1]

    if avg_move / price > 0.003:
        volatility = "HIGH"
    else:
        volatility = "LOW"

    # ===== НОЧНОЙ РЕЖИМ =====
    from time import localtime
    hour = localtime().tm_hour
    night = hour >= 0 and hour <= 6

    return {
        "trend": trend,
        "volatility": volatility,
        "night": night
    }
