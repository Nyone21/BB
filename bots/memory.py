import json
import os
from time import time

MEMORY_FILE = "data/trade_memory.json"


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)


def remember_trade(
    symbol,
    signal,
    price,
    rsi,
    ema,
    confidence,
    result=None
):
    memory = load_memory()

    record = {
        "time": int(time()),
        "symbol": symbol,
        "signal": signal,
        "price": price,
        "rsi": rsi,
        "ema": ema,
        "confidence": confidence,
        "result": result  # None | profit | loss
    }

    memory.append(record)
    memory = memory[-1000:]

    save_memory(memory)


def update_trade_result(index, result):
    memory = load_memory()
    if 0 <= index < len(memory):
        memory[index]["result"] = result
        save_memory(memory)
