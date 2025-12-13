# config/settings.py - Настройки бота
from dataclasses import dataclass
from enum import Enum

class TradingMode(Enum):
    DEMO = "demo"
    PAPER = "paper"
    LIVE = "live"

class TimeFrame(Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

@dataclass
class BotConfig:
    # Режим работы
    MODE: TradingMode = TradingMode.DEMO
    SYMBOL: str = "BTCUSDT"
    TIMEFRAME: TimeFrame = TimeFrame.M15
    
    # Настройки анализа
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT: float = 70.0
    RSI_OVERSOLD: float = 30.0
    EMA_SHORT: int = 9
    EMA_LONG: int = 21
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    
    # Управление рисками
    MAX_POSITION_SIZE: float = 0.1  # 10% от баланса
    STOP_LOSS: float = 0.02  # 2%
    TAKE_PROFIT: float = 0.05  # 5%
    MAX_DAILY_LOSS: float = 0.1  # 10%
    
    # Настройки бота
    CHECK_INTERVAL: int = 60  # секунды
    ENABLE_LOGGING: bool = True
    SAVE_LOGS: bool = True
    
    @classmethod
    def load_from_env(cls):
        """Загрузка настроек из .env файла"""
        # Здесь можно добавить загрузку из .env
        return cls()