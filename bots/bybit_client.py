# bots/bybit_client.py

import os
import time
import logging
from typing import Any

import requests
from requests.exceptions import RequestException
from pybit.unified_trading import HTTP

logger = logging.getLogger(__name__)

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
BYBIT_API_BASE = os.getenv("BYBIT_API_BASE", "https://api.bybit.com")


def _retry_request(func, *args, retries=3, backoff=1, **kwargs):
    last_exc = None
    for i in range(retries):
        try:
            return func(*args, **kwargs)
        except RequestException as e:
            last_exc = e
            sleep = backoff * (2 ** i)
            logger.warning("Bybit request failed (attempt %d): %s — retrying in %s s", i + 1, e, sleep)
            time.sleep(sleep)
        except Exception as e:
            last_exc = e
            logger.exception("Unexpected error in Bybit request")
            time.sleep(backoff)
    raise last_exc


def get_server_time():
    def _call():
        r = requests.get(f"{BYBIT_API_BASE}/v5/market/time", timeout=5)
        r.raise_for_status()
        return int(r.json()["result"]["timeSecond"]) * 1000

    return _retry_request(_call)


class SyncedSession(HTTP):
    def _get_timestamp(self):
        return get_server_time()


session = SyncedSession(
    api_key=API_KEY,
    api_secret=API_SECRET,
    testnet=(os.getenv("BYBIT_TESTNET", "false").lower() in ("1", "true")),
    recv_window=10000,
)


def get_balance():
    def _call():
        data = session.get_wallet_balance(accountType="UNIFIED")
        coins = data["result"]["list"][0]["coin"]
        for c in coins:
            if c["coin"] == "USDT":
                return float(c["walletBalance"])
        return 0.0

    return _retry_request(_call)


def get_positions(category: str = "linear", symbol: str | None = None, settleCoin: str | None = None):
    """Return positions list via Bybit API (best-effort).

    Returns list (may be empty) or raises on persistent errors.
    """
    def _call():
        params = {"category": category}
        if symbol:
            params["symbol"] = symbol
        # Bybit API often requires settleCoin for unified positions listing
        if settleCoin:
            params["settleCoin"] = settleCoin
        else:
            params.setdefault("settleCoin", "USDT")
        data = session.get_positions(**params)
        return data.get("result", {}).get("list", [])

    return _retry_request(_call)


def get_price(symbol: str, category: str = "spot") -> float:
    def _call():
        data = session.get_tickers(category=category, symbol=symbol)
        return float(data["result"]["list"][0]["lastPrice"])

    return _retry_request(_call)


def get_candles(symbol: str, interval: str = "5", limit: int = 50, category: str = "spot") -> Any:
    def _call():
        data = session.get_kline(
            category=category,
            symbol=symbol,
            interval=interval,
            limit=limit,
        )
        return data["result"]["list"]

    return _retry_request(_call)


def place_spot_order(symbol: str, side: str, usdt_amount: float) -> Any:
    price = get_price(symbol, "spot")
    qty = round(usdt_amount / price, 6)

    # Проверяем минимальный размер ордера для спотовых пар
    min_order_value = 5.0  # минимальная стоимость ордера в USDT
    if usdt_amount < min_order_value:
        # Увеличиваем размер ордера до минимального значения
        qty = round(min_order_value / price, 6)
        usdt_amount = qty * price

    def _call():
        order = session.place_order(
            category="spot",
            symbol=symbol,
            side=side,
            orderType="Market",
            qty=qty,
        )
        return order

    return _retry_request(_call)


def place_futures_order(symbol: str, side: str, qty: float, leverage: int = 1) -> Any:
    def _call():
        # Установка плеча
        session.set_leverage(
            category="linear",
            symbol=symbol,
            buyLeverage=str(leverage),
            sellLeverage=str(leverage)
        )
        
        order = session.place_order(
            category="linear",
            symbol=symbol,
            side=side,
            orderType="Market",
            qty=str(qty),
            timeInForce="IOC",
            positionIdx=0  # one-way trading
        )
        return order

    return _retry_request(_call)
