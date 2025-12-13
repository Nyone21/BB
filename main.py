import os
import time
from pybit.unified_trading import HTTP
from bots.analyzer import analyze_market
from bots.trader import place_order
from bots.risk_manager import calc_position

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

session = HTTP(
    testnet=True,
    api_key=API_KEY,
    api_secret=API_SECRET
)

def get_candles():
    data = session.get_kline(
        category="linear",
        symbol="BTCUSDT",
        interval="5",
        limit=100
    )
    return data["result"]["list"]

def main():
    print("=" * 50)
    print(" AUTO BYBIT BOT STARTED")
    print("=" * 50)

    while True:
        candles = get_candles()
        signal = analyze_market(candles)

        wallet = session.get_wallet_balance(accountType="UNIFIED")
        balance = float(wallet["result"]["list"][0]["totalWalletBalance"])

        print(f"Signal: {signal} | Balance: {balance}")

        if signal in ["BUY", "SELL"] and balance > 10:
            qty = calc_position(balance)
            place_order(session, signal, qty)

        time.sleep(60)

if __name__ == "__main__":
    main()
