import time
from bots.analyzer import analyze_market
from bots import bybit_client

def main():
    print("=" * 50)
    print("AUTO BYBIT BOT STARTED (RENDER)")
    print("=" * 50)

    while True:
        try:
            candles = bybit_client.get_candles()
            signal = analyze_market(candles)
            balance = bybit_client.get_balance()

            print(f"Signal: {signal} | Balance: {balance}")

            time.sleep(30)
        except Exception as e:
            print("ERROR:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
