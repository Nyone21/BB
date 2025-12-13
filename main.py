import time
from bots.analyzer import analyze_market
from bots.bybit_client import get_candles, get_balance

def main():
    print("="*50)
    print("AUTO BYBIT BOT STARTED (RAILWAY)")
    print("="*50)

    while True:
        try:
            candles = get_candles()
            signal = analyze_market(candles)
            balance = get_balance()

            print(f"Signal: {signal} | Balance: {balance}")

            time.sleep(30)  # каждые 30 секунд
        except Exception as e:
            print("ERROR:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
