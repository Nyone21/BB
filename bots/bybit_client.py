import os
from pybit.unified_trading import HTTP

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

# ❗️ЖЁСТКО отключаем testnet
BYBIT_TESTNET = False

session = HTTP(
    testnet=BYBIT_TESTNET,
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET,
)

def get_candles(symbol="BTCUSDT", interval="1", limit=50):
    return session.get_kline(
        category="spot",
        symbol=symbol,
        interval=interval,
        limit=limit
    )

def get_balance():
    return session.get_wallet_balance(accountType="UNIFIED")
