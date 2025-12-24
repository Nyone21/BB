import time

# ===== BOT FLAGS =====
BOT_ENABLED = True
TRADING_MODE = "AUTO"  # AUTO / SPOT / FUTURES
OPEN_TRADES = {}
# Runtime live flag: when True, bot executes real orders regardless of DRY_RUN env
LIVE = False
# ===== REPORTING =====
REPORT_INTERVAL = 15 * 60  # 15 минут
LAST_REPORT_TS = 0

# ===== MEMORY =====
last_balance = 0.0
open_positions = {}
