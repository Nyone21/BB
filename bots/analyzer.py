import numpy as np
from typing import Tuple, List

def calculate_atr(candles: List[List], period: int = 14) -> float:
    """Рассчитывает Average True Range для определения волатильности"""
    if len(candles) < period + 1:
        # Если недостаточно данных, используем простое среднее от разницы high-low
        total_range = sum(abs(float(candle[2]) - float(candle[3])) for candle in candles)
        return total_range / len(candles) if candles else 0.0
    
    true_ranges = []
    for i in range(1, min(len(candles), period + 1)):
        high = float(candles[i][2])
        low = float(candles[i][3])
        prev_close = float(candles[i-1][4])
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        true_ranges.append(tr)
    
    return sum(true_ranges) / len(true_ranges) if true_ranges else 0.0

def calculate_rsi(closes: np.ndarray, period: int = 14) -> float:
    """Рассчитывает RSI индикатор"""
    if len(closes) < period + 1:
        return 50.0  # нейтральное значение
    
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:]) if len(gains) >= period else np.mean(gains)
    avg_loss = np.mean(losses[-period:]) if len(losses) >= period else np.mean(losses)
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(closes: np.ndarray, fast: int = 12, slow: int = 26, signal_period: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Рассчитывает MACD индикатор"""
    def ema(values, period):
        ema_values = np.zeros_like(values)
        ema_values[0] = values[0]
        multiplier = 2 / (period + 1)
        for i in range(1, len(values)):
            ema_values[i] = (values[i] * multiplier) + (ema_values[i-1] * (1 - multiplier))
        return ema_values
    
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def analyze_market(candles: List[List]) -> Tuple[str, float, np.ndarray]:
    """Улучшенный анализ рынка с несколькими индикаторами"""
    closes = np.array([float(c[4]) for c in candles])
    highs = np.array([float(c[2]) for c in candles])
    lows = np.array([float(c[3]) for c in candles])

    # EMA (Exponential Moving Average) для тренда
    ema_period = 20
    ema = np.zeros_like(closes)
    ema[0] = closes[0]
    multiplier = 2 / (ema_period + 1)
    
    for i in range(1, len(closes)):
        ema[i] = (closes[i] * multiplier) + (ema[i-1] * (1 - multiplier))

    # Рассчитываем вспомогательные индикаторы
    atr = calculate_atr(candles)
    rsi = calculate_rsi(closes)
    macd_line, signal_line, histogram = calculate_macd(closes)
    
    current_price = closes[-1]
    current_ema = ema[-1]
    current_macd = macd_line[-1]
    current_signal = signal_line[-1]
    
    # Определяем сигнал на основе нескольких факторов
    trend_signal = ""
    if current_price > current_ema:
        trend_signal = "BUY"
    elif current_price < current_ema:
        trend_signal = "SELL"
    else:
        trend_signal = "HOLD"
    
    # MACD сигнал
    macd_signal = ""
    if current_macd > current_signal:
        macd_signal = "BUY"
    elif current_macd < current_signal:
        macd_signal = "SELL"
    else:
        macd_signal = "HOLD"
    
    # Дополнительные условия для фильтрации сигналов
    volatility_ok = atr > 0.01  # Проверяем, что есть достаточная волатильность
    momentum_ok = (rsi < 30 and trend_signal == "BUY") or (rsi > 70 and trend_signal == "SELL") or (30 <= rsi <= 70)
    
    # Комбинируем сигналы
    if volatility_ok and momentum_ok:
        # Если основной тренд и MACD дают одинаковый сигнал, усиливаем его
        if trend_signal == macd_signal and trend_signal != "HOLD":
            signal = trend_signal
        # Если RSI подтверждает перекупленность/перепроданность
        elif trend_signal != "HOLD" and ((rsi < 30 and trend_signal == "BUY") or (rsi > 70 and trend_signal == "SELL")):
            signal = trend_signal
        else:
            signal = "HOLD"
    else:
        signal = "HOLD"
    
    # Добавляем дополнительную проверку для подтверждения сигнала
    if signal != "HOLD":
        # Проверяем, что цена значительно отклонилась от EMA
        deviation = abs(current_price - current_ema) / current_price
        if deviation < 0.05:  # Меньше 0.5% - слишком мало для входа
            signal = "HOLD"
    
    return signal, current_ema, closes, highs, lows
