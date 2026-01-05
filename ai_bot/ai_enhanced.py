"""
Расширенная AI-логика для AI-бота.

Этот модуль предоставляет улучшенную AI-логику с обучением
на основе результатов сделок и адаптацией стратегии.
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
from bots.core.data_manager import DataManager


class AIBrain:
    """
    Улучшенный AI-мозг с обучением и адаптацией.
    """
    
    def __init__(self, data_manager: DataManager):
        """
        Инициализация AI-мозга.
        
        Args:
            data_manager: Менеджер данных для сохранения состояния
        """
        self.data_manager = data_manager
        # Используем тот же подход, что и в DataManager для получения пути к файлу
        bot_prefix = data_manager.bot_prefix
        data_dir = data_manager.data_dir
        if bot_prefix == "main_bot":
            self.brain_file = data_dir / "ai_brain.json"
        else:
            self.brain_file = data_dir / f"{bot_prefix}_ai_brain.json"
        
        self.default_confidence = {
            "BUY": 1.0,
            "SELL": 1.0,
            "HOLD": 1.0
        }
        self.load_brain()
    
    def load_brain(self) -> Dict:
        """Загрузить состояние AI-мозга."""
        if not self.brain_file.exists():
            self.brain = {
                "confidence": self.default_confidence.copy(),
                "win_trades": 0,
                "loss_trades": 0,
                "total_trades": 0,
                "patterns": {}  # Паттерны для обучения
            }
            self.save_brain()
            return self.brain
        
        try:
            with open(self.brain_file, "r", encoding="utf-8") as f:
                self.brain = json.load(f)
            # Убеждаемся, что все ключи присутствуют
            if "confidence" not in self.brain:
                self.brain["confidence"] = self.default_confidence.copy()
            if "patterns" not in self.brain:
                self.brain["patterns"] = {}
            return self.brain
        except (json.JSONDecodeError, FileNotFoundError):
            self.brain = {
                "confidence": self.default_confidence.copy(),
                "win_trades": 0,
                "loss_trades": 0,
                "total_trades": 0,
                "patterns": {}
            }
            self.save_brain()
            return self.brain
    
    def save_brain(self) -> None:
        """Сохранить состояние AI-мозга."""
        self.brain_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.brain_file, "w", encoding="utf-8") as f:
            json.dump(self.brain, f, indent=2, ensure_ascii=False)
    
    def decide(self, raw_signal: str, ai_signal: str) -> str:
        """
        Принять решение на основе сигналов и обучения.
        
        Args:
            raw_signal: Сырой сигнал от анализатора
            ai_signal: Сигнал от AI-фильтра
            
        Returns:
            str: Финальное решение (BUY/SELL/HOLD)
        """
        if ai_signal == "HOLD":
            return "HOLD"
        
        # Получаем уверенность для сигнала
        confidence = self.brain["confidence"].get(ai_signal, 1.0)
        
        # Если уверенность слишком низкая, не торгуем
        if confidence < 0.5:
            return "HOLD"
        
        # Если уверенность высокая и сигналы совпадают, торгуем
        if raw_signal == ai_signal and confidence >= 0.7:
            return ai_signal
        
        # Если уверенность средняя, торгуем с осторожностью
        if confidence >= 0.5:
            return ai_signal
        
        return "HOLD"
    
    def feedback(self, win: bool, signal: str) -> None:
        """
        Обратная связь для обучения на основе результата сделки.
        
        Args:
            win: True если сделка прибыльная, False если убыточная
            signal: Сигнал, который привел к сделке (BUY/SELL)
        """
        self.brain["total_trades"] += 1
        
        if win:
            self.brain["win_trades"] += 1
            # Увеличиваем уверенность в успешном сигнале
            if signal in self.brain["confidence"]:
                self.brain["confidence"][signal] = min(
                    2.0,
                    self.brain["confidence"][signal] + 0.05
                )
        else:
            self.brain["loss_trades"] += 1
            # Уменьшаем уверенность в неуспешном сигнале
            if signal in self.brain["confidence"]:
                self.brain["confidence"][signal] = max(
                    0.1,
                    self.brain["confidence"][signal] - 0.05
                )
        
        # Нормализуем уверенность
        for k in self.brain["confidence"]:
            self.brain["confidence"][k] = max(0.1, min(2.0, self.brain["confidence"][k]))
        
        self.save_brain()
    
    def get_stats(self) -> Dict:
        """Получить статистику AI-мозга."""
        total = self.brain["win_trades"] + self.brain["loss_trades"]
        winrate = (self.brain["win_trades"] / total * 100) if total > 0 else 0
        
        return {
            "total_trades": self.brain["total_trades"],
            "win_trades": self.brain["win_trades"],
            "loss_trades": self.brain["loss_trades"],
            "winrate": winrate,
            "confidence": self.brain["confidence"].copy()
        }


def update_trade_feedback(data_manager: DataManager, trade: Dict) -> None:
    """
    Обновить обратную связь для AI на основе завершенной сделки.
    
    Args:
        data_manager: Менеджер данных
        trade: Данные сделки с PnL
    """
    try:
        ai_brain = AIBrain(data_manager)
        signal = trade.get("side", "").upper()
        pnl = trade.get("pnl", 0.0)
        
        if signal in ("BUY", "SELL") and pnl != 0:
            win = pnl > 0
            ai_brain.feedback(win, signal)
    except Exception as e:
        print(f"Error updating AI feedback: {e}")

