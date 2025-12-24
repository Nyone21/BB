import os
import time
from typing import Tuple

RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.01"))
MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "0.05"))
MAX_TRADES_PER_DAY = int(os.getenv("MAX_TRADES_PER_DAY", "5"))

# daily state in-memory (reset every 24h)
_daily_state = {
    "day_start": int(time.time()),
    "loss": 0.0,
    "trades": 0,
}


def _reset_if_new_day():
    if time.time() - _daily_state["day_start"] > 24 * 3600:
        _daily_state["day_start"] = int(time.time())
        _daily_state["loss"] = 0.0
        _daily_state["trades"] = 0


def record_trade_result(pnl: float) -> None:
    """Record trade PnL (negative for loss)."""
    _reset_if_new_day()
    _daily_state["loss"] += min(0.0, pnl)
    _daily_state["trades"] += 1


def get_daily_loss() -> float:
    _reset_if_new_day()
    return _daily_state["loss"]


def get_trades_today() -> int:
    _reset_if_new_day()
    return _daily_state["trades"]


def allow_trade(balance: float) -> Tuple[bool, str]:
    _reset_if_new_day()
    if balance <= 0:
        return False, "no balance"
    if abs(_daily_state["loss"]) >= MAX_DAILY_LOSS * balance:
        return False, "daily loss limit reached"
    if _daily_state["trades"] >= MAX_TRADES_PER_DAY:
        return False, "max trades per day reached"
    return True, "ok"


def compute_trade_amount(balance: float) -> float:
    # Учитываем максимальное количество одновременных сделок
    max_trades = int(os.getenv("MAX_TRADES_PER_DAY", "5"))
    active_trades = _daily_state["trades"]
    
    # Динамически уменьшаем размер позиции при увеличении количества активных сделок
    risk_factor = 1.0 - min(0.7, (active_trades / max_trades) * 0.5)  # Уменьшаем риск до 50% при полной нагрузке
    base_amount = balance * RISK_PER_TRADE * risk_factor
    
    # Минимальный размер позиции
    min_position_size = 5.0  # минимальный размер позиции в USDT
    max_position_size = balance * 0.1  # максимальный размер позиции 10% от баланса
    
    trade_amount = max(min_position_size, min(base_amount, max_position_size))
    
    return trade_amount


def calc_sl_tp(price, atr, side):
    # Используем ATR для более адаптивного управления стопами
    # Динамически изменяем уровни стопа в зависимости от волатильности
    atr_multiplier_sl = max(1.5, min(3.0, atr * 1000))  # Увеличиваем стоп-лосс при высокой волатильности
    atr_multiplier_tp = atr_multiplier_sl * 1.8  # Соотношение стоп-лосс к тейк-профит 1:1.8
    
    if side == "BUY":
        sl = price - atr * atr_multiplier_sl
        tp = price + atr * atr_multiplier_tp
    else:
        sl = price + atr * atr_multiplier_sl
        tp = price - atr * atr_multiplier_tp
        
    # Проверяем, что стоп-лосс и тейк-профит находятся на безопасном расстоянии от цены
    min_sl_distance = price * 0.02  # 0.2% минимальное расстояние для стоп-лосс
    min_tp_distance = price * 0.03  # 0.3% минимальное расстояние для тейк-профит
    
    if side == "BUY":
        sl = min(sl, price - min_sl_distance)
        tp = max(tp, price + min_tp_distance)
    else:
        sl = max(sl, price + min_sl_distance)
        tp = min(tp, price - min_tp_distance)
    
    return round(sl, 2), round(tp, 2)
