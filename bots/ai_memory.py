import json
import os
import time

FILE = "data/ai_memory.json"


def load_memory():
    if not os.path.exists(FILE):
        return {"trades": [], "stats": {"wins": 0, "losses": 0}}

    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # Восстанавливаем файл с корректной структурой при ошибке
        save_memory({"trades": [], "stats": {"wins": 0, "losses": 0}})
        return {"trades": [], "stats": {"wins": 0, "losses": 0}}


def save_memory(memory):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)


def register_trade(symbol, side, entry, exit_price):
    memory = load_memory()

    pnl = exit_price - entry if side == "BUY" else entry - exit_price
    result = "WIN" if pnl > 0 else "LOSS"

    trade = {
        "time": int(time.time()),
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "exit": exit_price,
        "pnl": pnl,
        "result": result
    }

    memory["trades"].append(trade)

    if result == "WIN":
        memory["stats"]["wins"] += 1
    else:
        memory["stats"]["losses"] += 1

    save_memory(memory)
    return trade


def get_stats():
    memory = load_memory()
    wins = memory["stats"]["wins"]
    losses = memory["stats"]["losses"]
    total = wins + losses
    winrate = round((wins / total) * 100, 2) if total > 0 else 0

    return wins, losses, winrate
