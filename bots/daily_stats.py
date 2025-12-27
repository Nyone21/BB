import os
import json
import time
from datetime import datetime
from bots.telegram import notify_daily_report
from bots.trade_logger import load_memory

# Конфигурация
STATS_FILE = "data/daily_stats.json"

class DailyStats:
    def __init__(self):
        self.stats_file = STATS_FILE
        self.reset_daily_stats()
        self.load_stats()
        
        # Создаем директорию, если её нет
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
    
    def reset_daily_stats(self):
        """Сбросить дневную статистику"""
        self.daily_stats = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "total_pnl": 0.0,
            "best_trade": float('-inf'),
            "worst_trade": float('inf'),
            "max_drawdown": 0.0,
            "winrate": 0.0,
            "updated_at": time.time()
        }
    
    def is_new_day(self):
        """Проверить, наступило ли новое сутки"""
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        return current_date != self.daily_stats.get("date", "")
    
    def update_stats(self, pnl):
        """Обновить статистику по сделке"""
        if self.is_new_day():
            self.send_daily_report()
            self.reset_daily_stats()
        
        self.daily_stats["total_trades"] += 1
        if pnl > 0:
            self.daily_stats["wins"] += 1
        else:
            self.daily_stats["losses"] += 1
        
        self.daily_stats["total_pnl"] += pnl
        
        # Обновляем лучшую и худшую сделку
        if pnl > self.daily_stats["best_trade"]:
            self.daily_stats["best_trade"] = pnl
        if pnl < self.daily_stats["worst_trade"]:
            self.daily_stats["worst_trade"] = pnl
        
        # Обновляем просадку
        if pnl < self.daily_stats["max_drawdown"]:
            self.daily_stats["max_drawdown"] = pnl
        
        # Обновляем процент выигрышных сделок
        if self.daily_stats["total_trades"] > 0:
            self.daily_stats["winrate"] = (self.daily_stats["wins"] / self.daily_stats["total_trades"]) * 100
        
        self.daily_stats["updated_at"] = time.time()
        self.save_stats()
    
    def get_stats(self):
        """Получить текущую статистику"""
        if self.is_new_day():
            self.send_daily_report()
            self.reset_daily_stats()
        
        return self.daily_stats
    
    def save_stats(self):
        """Сохранить статистику в файл"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.daily_stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving daily stats: {e}")
    
    def load_stats(self):
        """Загрузить статистику из файла"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    loaded_stats = json.load(f)
                
                # Проверяем, если это статистика за текущий день
                if loaded_stats.get("date", "") == datetime.utcnow().strftime("%Y-%m-%d"):
                    self.daily_stats = loaded_stats
                else:
                    # Если это статистика за прошлый день, сбрасываем
                    self.reset_daily_stats()
        except Exception as e:
            print(f"Error loading daily stats: {e}")
            self.reset_daily_stats()
    
    def send_daily_report(self):
        """Отправить ежедневный отчет в Telegram"""
        if self.daily_stats["total_trades"] > 0:
            report_data = {
                "total_trades": self.daily_stats["total_trades"],
                "wins": self.daily_stats["wins"],
                "losses": self.daily_stats["losses"],
                "winrate": self.daily_stats["winrate"],
                "total_pnl": self.daily_stats["total_pnl"],
                "best_trade": self.daily_stats["best_trade"] if self.daily_stats["best_trade"] != float('-inf') else 0,
                "worst_trade": self.daily_stats["worst_trade"] if self.daily_stats["worst_trade"] != float('inf') else 0,
                "max_drawdown": self.daily_stats["max_drawdown"]
            }
            notify_daily_report(report_data)
    
    def check_and_reset_if_new_day(self):
        """Проверить, наступил ли новый день, и сбросить статистику при необходимости"""
        if self.is_new_day():
            self.send_daily_report()
            self.reset_daily_stats()
            return True
        return False

# Глобальный экземпляр для использования в других модулях
daily_stats = DailyStats()
