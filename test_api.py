# test_api_bybit.py — тест Bybit API v5
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os

print("=" * 60)
print("🔄 ТЕСТ BYBIT API v5")
print("=" * 60)

load_dotenv()

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

if not api_key or not api_secret:
    print("❌ Ключи BYBIT не найдены")
    exit()

print(f"API Key: {api_key[:10]}...")

try:
    session = HTTP(
        testnet=True,  # False для реального аккаунта
        api_key=api_key,
        api_secret=api_secret
    )

    print("\n1️⃣ Проверка публичных данных")
    ticker = session.get_tickers(
        category="linear",
        symbol="BTCUSDT"
    )
    price = ticker["result"]["list"][0]["lastPrice"]
    print(f"✅ BTCUSDT цена: {price}")

    print("\n2️⃣ Проверка баланса")
    balance = session.get_wallet_balance(
        accountType="UNIFIED"
    )

    usdt = balance["result"]["list"][0]["totalWalletBalance"]
    print(f"✅ Баланс USDT: {usdt}")

    print("\n3️⃣ Проверка позиций")
    positions = session.get_positions(
        category="linear",
        symbol="BTCUSDT"
    )
    print("✅ API работает, позиции получены")

    print("\n" + "=" * 60)
    print("🎉 BYBIT API РАБОТАЕТ КОРРЕКТНО")
    print("=" * 60)

except Exception as e:
    print(f"❌ Ошибка: {type(e).__name__}: {e}")
