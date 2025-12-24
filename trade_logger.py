import time
import json
from pathlib import Path

LOG_FILE = Path("data/trades.json")

def log_trade(data: dict):
    data["ts"] = int(time.time())

    if LOG_FILE.exists():
        try:
            trades = json.loads(LOG_FILE.read_text())
        except json.JSONDecodeError:
            trades = []
    else:
        trades = []

    trades.append(data)
    LOG_FILE.write_text(json.dumps(trades, indent=2))
