import os
import time
import numpy as np
from bots.trade_logger import load_memory
from bots import state
from bots import learning

# Configuration
COOLDOWN_SECS = int(os.getenv("TRADE_COOLDOWN", "30"))
MIN_HISTORY = int(os.getenv("AI_MIN_HISTORY", "5"))
WINRATE_THRESHOLD = float(os.getenv("AI_WINRATE_THRESHOLD", "0.3"))

# Новые параметры для усиленного фильтра
EMA_SHORT_PERIOD = int(os.getenv("EMA_SHORT_PERIOD", "50"))
EMA_LONG_PERIOD = int(os.getenv("EMA_LONG_PERIOD", "200"))
MIN_ATR_THRESHOLD = float(os.getenv("MIN_ATR_THRESHOLD", "0.001"))
FLAT_MARKET_THRESHOLD = float(os.getenv("FLAT_MARKET_THRESHOLD", "0.02"))  # 2% диапазон


def calculate_ema(closes, period):
    """Рассчитать EMA для заданного периода"""
    if len(closes) < period:
        return closes[-1] if closes else 0
    
    closes_array = np.array(closes[-period:])
    ema = np.mean(closes_array[:period])
    
    multiplier = 2 / (period + 1)
    for close in closes_array[period:]:
        ema = (close - ema) * multiplier + ema
    
    return ema


def calculate_atr(highs, lows, closes, period=14):
    """Рассчитать Average True Range"""
    if len(closes) < period:
        return 0.0
    
    true_ranges = []
    for i in range(1, min(len(highs), period)):
        high = highs[-i]
        low = lows[-i]
        prev_close = closes[-i-1]
        
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)
    
    if true_ranges:
        return sum(true_ranges) / len(true_ranges)
    return 0.0


def calculate_range_percentage(closes, period=100):
    """Рассчитать процентный диапазон для определения flat рынка"""
    if len(closes) < period:
        period = len(closes)
    
    if period == 0:
        return 0.0
    
    recent_closes = closes[-period:]
    high = max(recent_closes)
    low = min(recent_closes)
    
    if low == 0:
        return 0.0
    
    return (high - low) / low


def ai_filter(raw_signal, price, ema, closes, symbol, highs=None, lows=None):
    memory = load_memory()

    # If learning module explicitly disabled this signal, hold
    try:
        if not learning.is_signal_enabled(symbol, raw_signal):
            return "HOLD"
    except Exception:
        pass

    # 🧠 История только по этому символу
    history = [t for t in memory if t.get("symbol") == symbol]

    # если истории мало — возвращаем сырой сигнал
    if len(history) < MIN_HISTORY:
        return raw_signal

    # считаем успешность сигналов
    wins = [t for t in history if t.get("pnl", 0) > 0]
    winrate = len(wins) / len(history) if history else 0.0

    # 📉 если AI часто проигрывает — осторожнее
    if winrate < WINRATE_THRESHOLD:
        return "HOLD"

    # Ограничение по частоте торгов на один символ
    last_trade_ts = state.OPEN_TRADES.get(symbol)
    if last_trade_ts:
        if time.time() - last_trade_ts < COOLDOWN_SECS:
            return "HOLD"

    # Расчет EMA 50 и EMA 200 для фильтрации по тренду
    if len(closes) >= EMA_LONG_PERIOD:
        ema_short = calculate_ema(closes, EMA_SHORT_PERIOD)
        ema_long = calculate_ema(closes, EMA_LONG_PERIOD)
        
        # Фильтр по тренду: запрет BUY против нисходящего тренда, запрет SELL против восходящего
        if raw_signal == "BUY" and ema_short < ema_long:
            return "SKIP_TREND"  # Пропускаем покупку при нисходящем тренде
        
        if raw_signal == "SELL" and ema_short > ema_long:
            return "SKIP_TREND"  # Пропускаем продажу при восходящем тренде

    # Проверка волатильности через ATR
    if highs and lows and closes and len(highs) >= 14 and len(lows) >= 14 and len(closes) >= 14:
        atr = calculate_atr(highs, lows, closes, 14)
        if atr < MIN_ATR_THRESHOLD:
            return "SKIP_VOLATILITY"  # Слишком низкая волатильность

    # Фильтр flat-market (если range < X%)
    if len(closes) >= 100:
        range_pct = calculate_range_percentage(closes, 100)
        if range_pct < FLAT_MARKET_THRESHOLD:
            return "SKIP_FLAT"  # Рынок слишком плоский

    # Подтверждение тренда + сырой сигнал
    if raw_signal == "BUY" and price > ema:
        return "BUY"

    if raw_signal == "SELL" and price < ema:
        return "SELL"

    return "HOLD"
