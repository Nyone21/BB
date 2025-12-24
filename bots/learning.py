from bots.memory import load_memory


def evaluate_pattern(signal, rsi, confidence):
    memory = load_memory()

    similar = []
    for m in memory:
        if (
            m["signal"] == signal
            and abs(m["rsi"] - rsi) < 5
            and m["result"] is not None
        ):
            similar.append(m)

    if len(similar) < 5:
        return confidence, "Недостаточно истории"

    wins = sum(1 for m in similar if m["result"] == "profit")
    losses = sum(1 for m in similar if m["result"] == "loss")

    winrate = wins / (wins + losses)

    adjusted_conf = confidence
    reason = ""

    if winrate > 0.6:
        adjusted_conf += 10
        reason = f"🔥 Паттерн прибыльный ({int(winrate*100)}%)"
    elif winrate < 0.4:
        adjusted_conf -= 15
        reason = f"⚠️ Паттерн убыточный ({int(winrate*100)}%)"
    else:
        reason = f"➖ Нейтральный паттерн ({int(winrate*100)}%)"

    adjusted_conf = max(0, min(100, adjusted_conf))

    return adjusted_conf, reason


# --- New: simple statistics-driven signal disabling ---
import json
import os
from collections import defaultdict
from bots import trade_logger

STATS_FILE = "data/signal_stats.json"
MIN_TRADES = int(os.getenv("AI_MIN_HISTORY", "5"))
WINRATE_THRESHOLD = float(os.getenv("AI_WINRATE_THRESHOLD", "0.3"))
EXPECTANCY_THRESHOLD = float(os.getenv("AI_EXPECTANCY_THRESHOLD", "0.0"))


def update_stats():
    mem = trade_logger.load_memory()
    stats = defaultdict(lambda: {"wins": 0, "losses": 0, "pnl_sum": 0.0, "count": 0})

    for t in mem:
        sym = t.get("symbol")
        side = (t.get("side") or "").upper()
        if not sym or not side:
            continue
        key = f"{sym}|{side}"
        pnl = float(t.get("pnl", 0.0) or 0.0)
        stats[key]["count"] += 1
        stats[key]["pnl_sum"] += pnl
        if pnl > 0:
            stats[key]["wins"] += 1
        else:
            stats[key]["losses"] += 1

    out = {}
    for k, v in stats.items():
        count = v["count"]
        wins = v["wins"]
        pnl_sum = v["pnl_sum"]
        winrate = wins / count if count else 0.0
        expectancy = pnl_sum / count if count else 0.0
        out[k] = {"count": count, "wins": wins, "pnl_sum": pnl_sum, "winrate": winrate, "expectancy": expectancy}

    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
    except Exception:
        pass
    return out


def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def is_signal_enabled(symbol: str, side: str) -> bool:
    key = f"{symbol}|{side.upper()}"
    stats = load_stats()
    s = stats.get(key)
    if not s:
        return True
    if s.get("count", 0) < MIN_TRADES:
        return True
    if s.get("winrate", 0.0) < WINRATE_THRESHOLD and s.get("expectancy", 0.0) < EXPECTANCY_THRESHOLD:
        return False
    return True
