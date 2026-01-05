"""
Модуль состояния бота (обертка для обратной совместимости).

ВНИМАНИЕ: Этот модуль использует глобальное состояние для обратной совместимости.
Для новых проектов используйте bots.core.bot_state.BotState напрямую.

Этот модуль поддерживает старый API через глобальные переменные,
но внутри использует BotState для будущей миграции.
"""

import time
from bots.core.bot_state import BotState

# ===== ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР STATE (для будущего использования) =====
# Создаем глобальный экземпляр BotState для внутреннего использования
# Пока не используется напрямую, но готов для миграции
_global_bot_state = BotState()

# ===== ОБРАТНАЯ СОВМЕСТИМОСТЬ: ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====
# Сохраняем старый API для обратной совместимости
BOT_ENABLED = True
TRADING_MODE = "AUTO"  # AUTO / SPOT / FUTURES
OPEN_TRADES = {}
# Runtime live flag: when True, bot executes real orders regardless of DRY_RUN env
LIVE = False
# ===== REPORTING =====
REPORT_INTERVAL = 15 * 60  # 15 минут
LAST_REPORT_TS = 0

# ===== MEMORY =====
last_balance = 0.0
open_positions = {}

# ===== STATE DICTIONARY =====
# Dictionary to hold state for decision module
state = {
    "bot_enabled": BOT_ENABLED,
    "trading_mode": TRADING_MODE,
    "live": LIVE,
    "open_trades": OPEN_TRADES,
    "last_report_ts": LAST_REPORT_TS,
    "last_balance": last_balance,
    "open_positions": open_positions,
    "last_signal": "HOLD",      # Default signal
    "ai_signal": "HOLD",        # Default AI signal
    "trades": []                # List of executed trades
}


def update_state_dict():
    """
    Обновить словарь состояния с текущими значениями глобальных переменных.
    
    Эта функция сохраняет обратную совместимость со старым кодом.
    Также синхронизирует внутренний BotState для будущей миграции.
    """
    global state
    
    # Обновляем словарь состояния из глобальных переменных (старый API)
    state["bot_enabled"] = BOT_ENABLED
    state["trading_mode"] = TRADING_MODE
    state["live"] = LIVE
    state["open_trades"] = OPEN_TRADES
    state["last_report_ts"] = LAST_REPORT_TS
    state["last_balance"] = last_balance
    state["open_positions"] = open_positions
    
    # Синхронизируем внутренний BotState (для будущей миграции)
    _global_bot_state.bot_enabled = BOT_ENABLED
    _global_bot_state.trading_mode = TRADING_MODE
    _global_bot_state.live = LIVE
    _global_bot_state.open_trades = OPEN_TRADES
    _global_bot_state.last_report_ts = LAST_REPORT_TS
    _global_bot_state.last_balance = last_balance
    _global_bot_state.open_positions = open_positions
    _global_bot_state.update_state_dict()


def get_bot_state() -> BotState:
    """
    Получить глобальный экземпляр BotState.
    
    ВНИМАНИЕ: Эта функция для будущей миграции. Пока используйте
    глобальные переменные для обратной совместимости.
    
    Returns:
        BotState: Глобальный экземпляр состояния бота
    """
    update_state_dict()  # Синхронизируем перед возвратом
    return _global_bot_state
