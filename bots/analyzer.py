import pandas as pd

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def analyze_market(candles):
    # candles: list of lists from Bybit
    df = pd.DataFrame(
        candles,
        columns=["time", "open", "high", "low", "close", "volume", "turnover"]
    )

    df["close"] = df["close"].astype(float)

    df["ema_fast"] = ema(df["close"], 9)
    df["ema_slow"] = ema(df["close"], 21)
    df["rsi"] = rsi(df["close"])

    last = df.iloc[-1]

    if last["ema_fast"] > last["ema_slow"] and last["rsi"] < 30:
        return "BUY"

    if last["ema_fast"] < last["ema_slow"] and last["rsi"] > 70:
        return "SELL"

    return "HOLD"
