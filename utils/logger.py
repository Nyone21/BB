# utils/logger.py - Логирование
import logging
import sys
from datetime import datetime
import json
import os

class TradingLogger:
    """Логгер для бота"""
    
    def __init__(self, name: str = "CryptoBot", log_dir: str = "logs", enable_file_logging: bool = True):
        self.name = name
        self.log_dir = log_dir
        self.enable_file_logging = enable_file_logging
        
        # Создаем директорию для логов
        if enable_file_logging:
            os.makedirs(log_dir, exist_ok=True)
        
        # Настройка логгера
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Консольный хендлер
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Файловый хендлер
        if enable_file_logging:
            log_file = os.path.join(
                log_dir, 
                f"bot_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        """Информационное сообщение"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Предупреждение"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Ошибка"""
        self.logger.error(message)
    
    def signal(self, signal_data: dict):
        """Логирование сигнала"""
        message = f"📢 СИГНАЛ: {signal_data.get('signal')} | "
        message += f"Уверенность: {signal_data.get('confidence', 0):.2f} | "
        message += f"Цена: {signal_data.get('price', 0):.2f}"
        self.logger.info(message)
    
    def trade(self, trade_data: dict):
        """Логирование сделки"""
        message = f"💰 СДЕЛКА: {trade_data.get('action')} | "
        message += f"Цена: {trade_data.get('price', 0):.2f} | "
        message += f"Размер: {trade_data.get('size', 0):.6f}"
        
        if 'pnl' in trade_data:
            pnl = trade_data['pnl']
            pnl_str = f"+{pnl:.2f}" if pnl > 0 else f"{pnl:.2f}"
            message += f" | P&L: {pnl_str}"
        
        self.logger.info(message)