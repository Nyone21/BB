import os
import time
from typing import Tuple
from bots.telegram import notify_risk_block

RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.01"))
MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "0.05"))  # в процентах от баланса
MAX_DAILY_LOSS_USDT = float(os.getenv("MAX_DAILY_LOSS_USDT", "0"))  # фиксированная сумма в USDT (0 = отключено)
MAX_TRADES_PER_DAY = int(os.getenv("MAX_TRADES_PER_DAY", "5"))
MAX_CONSECUTIVE_LOSSES = int(os.getenv("MAX_CONSECUTIVE_LOSSES", "3"))

# daily state in-memory (reset every 24h)
_daily_state = {
    "day_start": int(time.time()),
    "loss": 0.0,
    "trades": 0,
    "consecutive_losses": 0,
    "trading_blocked": False,
    "block_reason": ""
}


def _reset_if_new_day():
    if time.time() - _daily_state["day_start"] > 24 * 3600:
        _daily_state["day_start"] = int(time.time())
        _daily_state["loss"] = 0.0
        _daily_state["trades"] = 0
        _daily_state["consecutive_losses"] = 0
        _daily_state["trading_blocked"] = False
        _daily_state["block_reason"] = ""


def record_trade_result(pnl: float) -> None:
    """Record trade PnL (negative for loss)."""
    _reset_if_new_day()
    
    # Обновляем статистику убытков
    if pnl < 0:
        _daily_state["loss"] += pnl
        _daily_state["consecutive_losses"] += 1
    else:
        _daily_state["consecutive_losses"] = 0
    
    _daily_state["trades"] += 1
    
    # Получаем актуальный баланс для проверки лимитов
    try:
        from bots.bybit_client import get_balance
        balance = get_balance()
    except Exception:
        # Если не удается получить баланс, используем заглушку
        balance = 100.0
    
    # Проверяем лимиты и блокируем торговлю при необходимости
    check_daily_limits(balance)
    
    # Обновляем дневную статистику
    try:
        from bots.daily_stats import daily_stats
        daily_stats.update_stats(pnl)
    except ImportError:
        pass # daily_stats может не быть доступен в некоторых контекстах


def get_daily_loss() -> float:
    _reset_if_new_day()
    return _daily_state["loss"]


def get_trades_today() -> int:
    _reset_if_new_day()
    return _daily_state["trades"]


def get_consecutive_losses() -> int:
    _reset_if_new_day()
    return _daily_state["consecutive_losses"]


def check_daily_limits(balance: float) -> Tuple[bool, str]:
    """Проверить дневные лимиты и при необходимости заблокировать торговлю"""
    _reset_if_new_day()
    
    # Проверяем лимит на дневной убыток (в процентах от баланса)
    if abs(_daily_state["loss"]) >= MAX_DAILY_LOSS * balance:
        if not _daily_state["trading_blocked"]:
            _daily_state["trading_blocked"] = True
            _daily_state["block_reason"] = "daily loss limit (percentage) reached"
            notify_risk_block(f"Дневной лимит убытка превышен (по проценту): {_daily_state['loss']:.4f} USDT")
        return False, "daily loss limit (percentage) reached"
    
    # Проверяем лимит на дневной убыток (в фиксированной сумме USDT)
    if MAX_DAILY_LOSS_USDT > 0 and abs(_daily_state["loss"]) >= MAX_DAILY_LOSS_USDT:
        if not _daily_state["trading_blocked"]:
            _daily_state["trading_blocked"] = True
            _daily_state["block_reason"] = "daily loss limit (fixed amount) reached"
            notify_risk_block(f"Дневной лимит убытка превышен (по фиксированной сумме): {_daily_state['loss']:.4f} USDT")
        return False, "daily loss limit (fixed amount) reached"
    
    # Проверяем лимит на количество сделок в день
    if _daily_state["trades"] >= MAX_TRADES_PER_DAY:
        if not _daily_state["trading_blocked"]:
            _daily_state["trading_blocked"] = True
            _daily_state["block_reason"] = "max trades per day reached"
            notify_risk_block(f"Достигнут лимит на количество сделок в день: {_daily_state['trades']}")
        return False, "max trades per day reached"
    
    # Проверяем лимит на количество последовательных убытков
    if _daily_state["consecutive_losses"] >= MAX_CONSECUTIVE_LOSSES:
        if not _daily_state["trading_blocked"]:
            _daily_state["trading_blocked"] = True
            _daily_state["block_reason"] = "max consecutive losses reached"
            notify_risk_block(f"Достигнут лимит на количество последовательных убытков: {_daily_state['consecutive_losses']}")
        return False, "max consecutive losses reached"
    
    return True, "ok"


def allow_trade(balance: float) -> Tuple[bool, str]:
    _reset_if_new_day()
    
    if balance <= 0:
        return False, "no balance"
    
    # Проверяем, не заблокирована ли торговля
    if _daily_state["trading_blocked"]:
        return False, _daily_state["block_reason"]
    
    # Проверяем дневные лимиты
    return check_daily_limits(balance)


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
