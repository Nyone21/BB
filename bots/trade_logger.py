import json
import os
from datetime import datetime
from bots.daily_stats import daily_stats

MEMORY_FILE = "data/ai_memory.json"


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        # Восстанавливаем файл с корректной структурой при ошибке
        os.makedirs("data", exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        return []


def save_trade(trade: dict):
    memory = load_memory()
    memory.append(trade)

    os.makedirs("data", exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)
    
    # Обновляем дневную статистику, если есть PnL
    if "pnl" in trade and trade["pnl"] is not None:
        daily_stats.update_stats(float(trade["pnl"]))


def log_trade(symbol, side, price, pnl):
    trade = {
        "symbol": symbol,
        "side": side,
        "price": price,
        "pnl": pnl,
        "time": datetime.utcnow().isoformat()
    }
    save_trade(trade)


def get_trades_since(since_ts: float):
    """Return trades with timestamp >= since_ts (epoch seconds).

    If since_ts is 0 or None, return all trades.
    """
    trades = load_memory()
    if not since_ts:
        return trades

    out = []
    for t in trades:
        ts_str = t.get("time")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str).timestamp()
        except Exception:
            continue
        if ts >= since_ts:
            out.append(t)
    return out


def attach_pnl_to_last_trade(pnl: float) -> bool:
    """Attach realized `pnl` to the most recent trade without pnl recorded.

    Returns True if a trade was updated.
    """
    memory = load_memory()
    # find last trade without explicit pnl or with pnl == 0.0
    for t in reversed(memory):
        if t.get("pnl") in (None, 0.0):
            t["pnl"] = float(pnl)
            try:
                with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(memory, f, indent=2)
                # Обновляем дневную статистику
                daily_stats.update_stats(float(pnl))
                return True
            except Exception:
                return False
    return False
