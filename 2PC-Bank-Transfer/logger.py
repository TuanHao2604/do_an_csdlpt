"""
Shared Logging Module
Module ghi log dùng chung cho toàn hệ thống
"""

import logging
import os
from datetime import datetime


class SystemLogger:
    """Centralized logging system for 2PC Bank Transfer"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.logs_dir = 'logs'
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        
        self.loggers = {}
        self._initialized = True
    
    def get_logger(self, name, log_file=None):
        """
        Get or create a logger instance
        """
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add file handler
        if log_file is None:
            log_file = f"{name}.log"
        
        log_path = os.path.join(self.logs_dir, log_file)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        self.loggers[name] = logger
        return logger

    def log_event(self, name: str, event: dict, log_file: str | None = None):
        """Append a JSON event to an event log file."""
        import json

        if log_file is None:
            log_file = f"{name}.events.log"

        log_path = os.path.join(self.logs_dir, log_file)
        # Ensure any necessary directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False))
            f.write("\n")

    def read_events(self, name: str, log_file: str | None = None) -> list[dict]:
        """Read all events from the named event log file."""
        import json

        if log_file is None:
            log_file = f"{name}.events.log"

        log_path = os.path.join(self.logs_dir, log_file)
        if not os.path.exists(log_path):
            return []

        events = []
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:
                    # skip malformed lines
                    continue
        return events


# Global logger instance
system_logger = SystemLogger()

# Convenience functions
def get_logger(name, log_file=None):
    """Get a logger instance"""
    return system_logger.get_logger(name, log_file)


def log_event(name, event: dict, log_file: str | None = None):
    """Append a JSON event line to the named event log file."""
    return system_logger.log_event(name, event, log_file)


def read_events(name, log_file: str | None = None) -> list[dict]:
    """Read back all JSON event lines from the named event log file."""
    return system_logger.read_events(name, log_file)
