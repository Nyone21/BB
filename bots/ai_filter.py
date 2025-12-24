import os
import time
from bots.trade_logger import load_memory
from bots import state
from bots import learning

# Configuration
COOLDOWN_SECS = int(os.getenv("TRADE_COOLDOWN", "300"))
MIN_HISTORY = int(os.getenv("AI_MIN_HISTORY", "5"))
WINRATE_THRESHOLD = float(os.getenv("AI_WINRATE_THRESHOLD", "0.3"))


def ai_filter(raw_signal, price, ema, closes, symbol):
    memory = load_memory()

    # If learning module explicitly disabled this signal, hold
    try:
        if not learning.is_signal_enabled(symbol, raw_signal):
            return "HOLD"
    except Exception:
        pass

    # 🧠 История только по этому символу
    history = [t for t in memory if t.get("symbol") == symbol]

    # если истории мало — возвращаем сырой сигнал
    if len(history) < MIN_HISTORY:
        return raw_signal

    # считаем успешность сигналов
    wins = [t for t in history if t.get("pnl", 0) > 0]
    winrate = len(wins) / len(history) if history else 0.0

    # 📉 если AI часто проигрывает — осторожнее
    if winrate < WINRATE_THRESHOLD:
        return "HOLD"

    # Ограничение по частоте торгов на один символ
    last_trade_ts = state.OPEN_TRADES.get(symbol)
    if last_trade_ts:
        if time.time() - last_trade_ts < COOLDOWN_SECS:
            return "HOLD"

    # Подтверждение тренда + сырой сигнал
    if raw_signal == "BUY" and price > ema:
        return "BUY"

    if raw_signal == "SELL" and price < ema:
        return "SELL"

    return "HOLD"
