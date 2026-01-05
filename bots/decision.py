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
    if not s.get("bot_enabled", True):
        return False, "BOT_DISABLED"

    # 2. нет сигнала
    if s.get("last_signal", "HOLD") == "HOLD":
        return False, "NO_SIGNAL"

    # 3. AI не подтверждает
    if s.get("last_signal", "HOLD") != s.get("ai_signal", "HOLD"):
        return False, "AI_DISAGREE"

    # 4. недостаточно баланса
    if s.get("last_balance", 0.0) < MIN_BALANCE:
        return False, "LOW_BALANCE"

    # 5. кулдаун
    trades = s.get("trades", [])
    if trades:
        last_trade_time = trades[-1].get("time", 0)
        if time.time() - last_trade_time < COOLDOWN_SEC:
            return False, "COOLDOWN"

    # 6. флэт рынок
    if market_is_flat(candles):
        return False, "FLAT_MARKET"

    return True, "OK"
