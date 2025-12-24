import csv
import os
from datetime import datetime

LOG_FILE = "data/trades.csv"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "time", "symbol", "side", "price", "qty",
            "sl", "tp", "mode", "confidence"
        ])


def log_trade(symbol, side, price, qty, sl, tp, mode, confidence):
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().isoformat(),
            symbol, side, price, qty, sl, tp, mode, confidence
        ])

LAST_REPORT_TS = 0
REPORT_INTERVAL = 900

# ===== GLOBAL BOT STATE =====

# включен ли бот
BOT_ENABLED = True

# режим торговли
# AUTO / SPOT / FUTURES
TRADING_MODE = "AUTO"

# ===== REPORT CONTROL =====

# время последнего отчёта
LAST_REPORT_TS = 0

# интервал отчёта (15 минут)
REPORT_INTERVAL = 900

