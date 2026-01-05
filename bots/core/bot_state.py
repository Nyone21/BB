"""
Инкапсулированное состояние бота.

Этот модуль предоставляет класс BotState для управления состоянием бота
без использования глобальных переменных. Это позволяет запускать несколько
ботов параллельно с изолированным состоянием.
"""

import time
from typing import Dict, Optional


class BotState:
    """
    Инкапсулированное состояние торгового бота.
    
    Все состояние бота хранится в экземпляре этого класса, что позволяет
    запускать несколько ботов параллельно без конфликтов.
    """
    
    def __init__(self):
        """Инициализация состояния бота с дефолтными значениями."""
        # ===== BOT FLAGS =====
        self.bot_enabled: bool = True
        self.trading_mode: str = "AUTO"  # AUTO / SPOT / FUTURES
        self.open_trades: Dict[str, float] = {}  # symbol -> timestamp
        self.live: bool = False  # Runtime live flag
        
        # ===== REPORTING =====
        self.report_interval: int = 15 * 60  # 15 минут
        self.last_report_ts: float = 0.0
        
        # ===== MEMORY =====
        self.last_balance: float = 0.0
        self.open_positions: Dict = {}
        
        # ===== STATE DICTIONARY =====
        # Dictionary для совместимости с decision модулем
        self._state_dict: Dict = {
            "bot_enabled": self.bot_enabled,
            "trading_mode": self.trading_mode,
            "live": self.live,
            "open_trades": self.open_trades,
            "last_report_ts": self.last_report_ts,
            "last_balance": self.last_balance,
            "open_positions": self.open_positions,
            "last_signal": "HOLD",
            "ai_signal": "HOLD",
            "trades": []
        }
    
    def update_state_dict(self) -> None:
        """
        Обновить словарь состояния для совместимости со старым API.
        
        Этот метод синхронизирует внутренний словарь состояния с текущими
        значениями атрибутов класса.
        """
        self._state_dict["bot_enabled"] = self.bot_enabled
        self._state_dict["trading_mode"] = self.trading_mode
        self._state_dict["live"] = self.live
        self._state_dict["open_trades"] = self.open_trades
        self._state_dict["last_report_ts"] = self.last_report_ts
        self._state_dict["last_balance"] = self.last_balance
        self._state_dict["open_positions"] = self.open_positions
    
    @property
    def state(self) -> Dict:
        """
        Получить словарь состояния (для обратной совместимости).
        
        Returns:
            Dict: Словарь с текущим состоянием бота
        """
        self.update_state_dict()
        return self._state_dict
    
    def set_bot_enabled(self, enabled: bool) -> None:
        """Установить статус включения бота."""
        self.bot_enabled = enabled
        self.update_state_dict()
    
    def set_trading_mode(self, mode: str) -> None:
        """Установить режим торговли (AUTO/SPOT/FUTURES)."""
        self.trading_mode = mode.upper()
        self.update_state_dict()
    
    def set_live(self, live: bool) -> None:
        """Установить флаг LIVE режима."""
        self.live = live
        self.update_state_dict()
    
    def record_trade(self, symbol: str) -> None:
        """Записать время последней сделки для символа."""
        self.open_trades[symbol] = time.time()
        self.update_state_dict()
    
    def update_balance(self, balance: float) -> None:
        """Обновить последний известный баланс."""
        self.last_balance = balance
        self.update_state_dict()
    
    def update_positions(self, positions: Dict) -> None:
        """Обновить открытые позиции."""
        self.open_positions = positions
        self.update_state_dict()
    
    def update_last_report_time(self) -> None:
        """Обновить время последнего отчета."""
        self.last_report_ts = time.time()
        self.update_state_dict()
    
    def get_trade_cooldown(self, symbol: str, cooldown_sec: float) -> bool:
        """
        Проверить, прошло ли достаточно времени с последней сделки.
        
        Args:
            symbol: Символ для проверки
            cooldown_sec: Время кулдауна в секундах
            
        Returns:
            bool: True если можно торговать, False если кулдаун активен
        """
        last_trade_ts = self.open_trades.get(symbol)
        if last_trade_ts is None:
            return True
        return (time.time() - last_trade_ts) >= cooldown_sec
    
    def reset(self) -> None:
        """Сбросить состояние бота к дефолтным значениям (для тестирования)."""
        self.__init__()

