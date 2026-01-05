"""
Фабрика для создания изолированных клиентов Bybit.

Этот модуль предоставляет возможность создавать отдельные сессии Bybit
для разных ботов, что позволяет использовать разные API ключи и настройки.
"""

import os
import time
import logging
import requests
from requests.exceptions import RequestException
from typing import Optional
from pybit.unified_trading import HTTP

logger = logging.getLogger(__name__)


def get_server_time(api_base: str = None) -> int:
    """
    Получить время сервера Bybit.
    
    Args:
        api_base: Базовый URL API (по умолчанию из env или стандартный)
        
    Returns:
        int: Timestamp в миллисекундах
    """
    if api_base is None:
        api_base = os.getenv("BYBIT_API_BASE", "https://api.bybit.com")
    
    r = requests.get(f"{api_base}/v5/market/time", timeout=5)
    r.raise_for_status()
    return int(r.json()["result"]["timeSecond"]) * 1000


class SyncedSession(HTTP):
    """
    Сессия Bybit с синхронизацией времени сервера.
    """
    
    def __init__(self, api_base: Optional[str] = None, *args, **kwargs):
        """
        Инициализация синхронизированной сессии.
        
        Args:
            api_base: Базовый URL API
            *args, **kwargs: Дополнительные аргументы для HTTP
        """
        self._api_base = api_base or os.getenv("BYBIT_API_BASE", "https://api.bybit.com")
        super().__init__(*args, **kwargs)
    
    def _get_timestamp(self):
        """Переопределение для использования синхронизированного времени сервера."""
        return get_server_time(self._api_base)


def create_bybit_session(
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    api_base: Optional[str] = None,
    testnet: Optional[bool] = None,
    recv_window: int = 10000
) -> SyncedSession:
    """
    Создать новую сессию Bybit с указанными параметрами.
    
    Args:
        api_key: API ключ (по умолчанию из BYBIT_API_KEY env)
        api_secret: API секрет (по умолчанию из BYBIT_API_SECRET env)
        api_base: Базовый URL API (по умолчанию из BYBIT_API_BASE env)
        testnet: Использовать testnet (по умолчанию из BYBIT_TESTNET env)
        recv_window: Окно получения в миллисекундах
        
    Returns:
        SyncedSession: Настроенная сессия Bybit
        
    Example:
        >>> session = create_bybit_session()
        >>> # Или с кастомными ключами:
        >>> ai_session = create_bybit_session(
        ...     api_key="AI_BOT_KEY",
        ...     api_secret="AI_BOT_SECRET"
        ... )
    """
    if api_key is None:
        api_key = os.getenv("BYBIT_API_KEY")
    if api_secret is None:
        api_secret = os.getenv("BYBIT_API_SECRET")
    if api_base is None:
        api_base = os.getenv("BYBIT_API_BASE", "https://api.bybit.com")
    if testnet is None:
        testnet = os.getenv("BYBIT_TESTNET", "false").lower() in ("1", "true")
    
    if not api_key or not api_secret:
        raise ValueError(
            "BYBIT_API_KEY and BYBIT_API_SECRET must be provided "
            "either as arguments or environment variables"
        )
    
    return SyncedSession(
        api_base=api_base,
        api_key=api_key,
        api_secret=api_secret,
        testnet=testnet,
        recv_window=recv_window
    )


# Глобальная сессия для обратной совместимости (ленивая инициализация)
_global_session: Optional[SyncedSession] = None


def get_global_session() -> SyncedSession:
    """
    Получить глобальную сессию Bybit (ленивая инициализация).
    
    Эта функция создает сессию при первом вызове, используя переменные окружения.
    Используется для обратной совместимости со старым кодом.
    
    Returns:
        SyncedSession: Глобальная сессия Bybit
    """
    global _global_session
    if _global_session is None:
        _global_session = create_bybit_session()
    return _global_session


def reset_global_session() -> None:
    """
    Сбросить глобальную сессию (для тестирования).
    
    ВНИМАНИЕ: Используйте только для тестирования!
    """
    global _global_session
    _global_session = None

