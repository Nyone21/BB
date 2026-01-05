"""
Контекст бота для централизованного управления всеми компонентами.

BotContext объединяет состояние бота, менеджер данных и клиент Bybit,
предоставляя изолированный контекст для каждого экземпляра бота.
"""

import os
from typing import Optional
from bots.core.bot_state import BotState
from bots.core.data_manager import DataManager
from bots.core.bybit_client_factory import create_bybit_session, SyncedSession


class BotContext:
    """
    Контекст бота - централизованное управление всеми компонентами.
    
    Каждый экземпляр BotContext изолирован и может использоваться
    для запуска отдельного бота с собственным состоянием, данными и API ключами.
    """
    
    def __init__(
        self,
        bot_name: str = "main_bot",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_base: Optional[str] = None,
        testnet: Optional[bool] = None,
        data_dir: str = "data"
    ):
        """
        Инициализация контекста бота.
        
        Args:
            bot_name: Имя бота (используется как префикс для файлов данных)
            api_key: API ключ Bybit (по умолчанию из env)
            api_secret: API секрет Bybit (по умолчанию из env)
            api_base: Базовый URL API (по умолчанию из env)
            testnet: Использовать testnet (по умолчанию из env)
            data_dir: Директория для хранения данных
        """
        self.bot_name = bot_name
        
        # Инициализация компонентов
        self.state = BotState()
        self.data_manager = DataManager(bot_prefix=bot_name, data_dir=data_dir)
        
        # Ленивая инициализация сессии Bybit
        self._session: Optional[SyncedSession] = None
        self._api_key = api_key
        self._api_secret = api_secret
        self._api_base = api_base
        self._testnet = testnet
    
    @property
    def session(self) -> SyncedSession:
        """
        Получить сессию Bybit (ленивая инициализация).
        
        Returns:
            SyncedSession: Сессия Bybit для этого бота
        """
        if self._session is None:
            self._session = create_bybit_session(
                api_key=self._api_key,
                api_secret=self._api_secret,
                api_base=self._api_base,
                testnet=self._testnet
            )
        return self._session
    
    def reset_session(self) -> None:
        """Сбросить сессию Bybit (для переподключения)."""
        self._session = None
    
    def get_state_dict(self) -> dict:
        """
        Получить словарь состояния (для совместимости со старым API).
        
        Returns:
            dict: Словарь с текущим состоянием бота
        """
        return self.state.state
    
    def configure_from_env(self) -> None:
        """
        Настроить контекст из переменных окружения.
        
        Читает стандартные переменные окружения и применяет их к контексту.
        """
        # Настройка режима торговли
        trading_mode = os.getenv("TRADE_MODE", "AUTO").upper()
        self.state.set_trading_mode(trading_mode)
        
        # Настройка DRY_RUN / LIVE
        dry_run = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
        self.state.set_live(not dry_run)
        
        # Настройка включения бота
        bot_enabled = os.getenv("BOT_ENABLED", "True").lower() in ("1", "true", "yes")
        self.state.set_bot_enabled(bot_enabled)
    
    def __repr__(self) -> str:
        """Строковое представление контекста."""
        return (
            f"BotContext(bot_name='{self.bot_name}', "
            f"enabled={self.state.bot_enabled}, "
            f"mode={self.state.trading_mode}, "
            f"live={self.state.live})"
        )


# Глобальный контекст для обратной совместимости (main_bot)
_global_context: Optional[BotContext] = None


def get_global_context() -> BotContext:
    """
    Получить глобальный контекст бота (ленивая инициализация).
    
    Эта функция создает контекст при первом вызове, используя переменные окружения.
    Используется для обратной совместимости со старым кодом.
    
    Returns:
        BotContext: Глобальный контекст бота
    """
    global _global_context
    if _global_context is None:
        _global_context = BotContext(bot_name="main_bot")
        _global_context.configure_from_env()
    return _global_context


def reset_global_context() -> None:
    """
    Сбросить глобальный контекст (для тестирования).
    
    ВНИМАНИЕ: Используйте только для тестирования!
    """
    global _global_context
    _global_context = None

