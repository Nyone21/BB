"""
Менеджер данных для изоляции файлов разных ботов.

Этот модуль предоставляет DataManager для управления файлами данных
с поддержкой префиксов, что позволяет запускать несколько ботов
параллельно без конфликтов в файлах данных.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class DataManager:
    """
    Менеджер данных с поддержкой префиксов для изоляции ботов.
    
    Каждый экземпляр DataManager использует префикс для всех файлов данных,
    что позволяет запускать несколько ботов параллельно без конфликтов.
    """
    
    def __init__(self, bot_prefix: str = "main_bot", data_dir: str = "data"):
        """
        Инициализация менеджера данных.
        
        Args:
            bot_prefix: Префикс для файлов этого бота (например, "main_bot", "ai_bot")
            data_dir: Директория для хранения данных
        """
        self.bot_prefix = bot_prefix
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, filename: str) -> Path:
        """
        Получить полный путь к файлу с учетом префикса.
        
        Args:
            filename: Имя файла (например, "ai_memory.json")
            
        Returns:
            Path: Полный путь к файлу
        """
        # Если префикс "main_bot", используем оригинальные имена для обратной совместимости
        if self.bot_prefix == "main_bot":
            return self.data_dir / filename
        else:
            # Для других ботов добавляем префикс
            name, ext = os.path.splitext(filename)
            return self.data_dir / f"{self.bot_prefix}_{name}{ext}"
    
    def load_memory(self, default: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        Загрузить историю сделок из файла.
        
        Args:
            default: Значение по умолчанию, если файл не существует
            
        Returns:
            List[Dict]: Список сделок
        """
        if default is None:
            default = []
        
        file_path = self._get_file_path("ai_memory.json")
        
        if not file_path.exists():
            return default
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else default
        except (json.JSONDecodeError, FileNotFoundError):
            # Восстанавливаем файл с корректной структурой при ошибке
            self.save_memory(default)
            return default
    
    def save_memory(self, memory: List[Dict[str, Any]]) -> None:
        """
        Сохранить историю сделок в файл.
        
        Args:
            memory: Список сделок для сохранения
        """
        file_path = self._get_file_path("ai_memory.json")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
    
    def append_trade(self, trade: Dict[str, Any]) -> None:
        """
        Добавить сделку в историю.
        
        Args:
            trade: Словарь с данными сделки
        """
        memory = self.load_memory()
        memory.append(trade)
        self.save_memory(memory)
    
    def load_daily_stats(self, default: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Загрузить дневную статистику из файла.
        
        Args:
            default: Значение по умолчанию, если файл не существует
            
        Returns:
            Dict: Словарь со статистикой
        """
        if default is None:
            default = {
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "total_pnl": 0.0,
                "best_trade": float('-inf'),
                "worst_trade": float('inf'),
                "max_drawdown": 0.0,
                "winrate": 0.0,
                "updated_at": 0.0
            }
        
        file_path = self._get_file_path("daily_stats.json")
        
        if not file_path.exists():
            return default
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return default
    
    def save_daily_stats(self, stats: Dict[str, Any]) -> None:
        """
        Сохранить дневную статистику в файл.
        
        Args:
            stats: Словарь со статистикой
        """
        file_path = self._get_file_path("daily_stats.json")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    
    def load_signal_stats(self, default: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Загрузить статистику сигналов из файла.
        
        Args:
            default: Значение по умолчанию, если файл не существует
            
        Returns:
            Dict: Словарь со статистикой сигналов
        """
        if default is None:
            default = {}
        
        file_path = self._get_file_path("signal_stats.json")
        
        if not file_path.exists():
            return default
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return default
    
    def save_signal_stats(self, stats: Dict[str, Any]) -> None:
        """
        Сохранить статистику сигналов в файл.
        
        Args:
            stats: Словарь со статистикой сигналов
        """
        file_path = self._get_file_path("signal_stats.json")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    
    def get_trades_since(self, since_ts: float) -> List[Dict[str, Any]]:
        """
        Получить сделки с момента времени.
        
        Args:
            since_ts: Timestamp в секундах (epoch)
            
        Returns:
            List[Dict]: Список сделок после указанного времени
        """
        memory = self.load_memory()
        if not since_ts:
            return memory
        
        out = []
        for t in memory:
            ts_str = t.get("time")
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00')).timestamp()
            except Exception:
                try:
                    ts = datetime.fromisoformat(ts_str).timestamp()
                except Exception:
                    continue
            if ts >= since_ts:
                out.append(t)
        return out
    
    def attach_pnl_to_last_trade(self, pnl: float) -> bool:
        """
        Прикрепить PnL к последней сделке без PnL.
        
        Args:
            pnl: Значение PnL
            
        Returns:
            bool: True если сделка была обновлена
        """
        memory = self.load_memory()
        # Находим последнюю сделку без PnL или с PnL == 0.0
        for t in reversed(memory):
            if t.get("pnl") in (None, 0.0):
                t["pnl"] = float(pnl)
                self.save_memory(memory)
                return True
        return False


# Глобальный экземпляр для обратной совместимости (main_bot)
_global_data_manager = DataManager(bot_prefix="main_bot")


def get_data_manager(bot_prefix: str = "main_bot") -> DataManager:
    """
    Получить DataManager для указанного бота.
    
    Args:
        bot_prefix: Префикс бота (по умолчанию "main_bot" для обратной совместимости)
        
    Returns:
        DataManager: Экземпляр менеджера данных
    """
    if bot_prefix == "main_bot":
        return _global_data_manager
    else:
        return DataManager(bot_prefix=bot_prefix)

