import time
from bots import state

MIN_BALANCE = 10.0        # минимум для торговли
COOLDOWN_SEC = 60 * 5     # 5 минут между сделками
MIN_VOLATILITY = 0.001   # фильтр флэта

def market_is_flat(candles):
    closes = [float(c[4]) for c in candles[-20:]]
    avg = sum(closes) / len(closes)
    spread = max(closes) - min(closes)
    return (spread / avg) < MIN_VOLATILITY


def can_trade(candles):
    s = state.state

    # 1. бот выключен
    if not s["bot_enabled"]:
        return False, "BOT_DISABLED"

    # 2. нет сигнала
    if s["last_signal"] == "HOLD":
        return False, "NO_SIGNAL"

    # 3. AI не подтверждает
    if s["last_signal"] != s["ai_signal"]:
        return False, "AI_DISAGREE"

    # 4. недостаточно баланса
    if s["last_balance"] < MIN_BALANCE:
        return False, "LOW_BALANCE"

    # 5. кулдаун
    if s["trades"]:
        last_trade_time = s["trades"][-1]["time"]
        if time.time() - last_trade_time < COOLDOWN_SEC:
            return False, "COOLDOWN"

    # 6. флэт рынок
    if market_is_flat(candles):
        return False, "FLAT_MARKET"

    return True, "OK"
