import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class JSONFileHandler(logging.Handler):
    def __init__(self, filename="logs.json"):
        super().__init__()
        self.filename = filename
        self.logs = []

        #create the file with empty array if not exist
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump([], f)
        else:
            # Load Existing logs
            try:
                with open(filename, 'r') as f:
                    self.logs = json.load(f)
            except json.JSONDecodeError:
                # if the file is corrupted start fresh
                self.logs = []

    def emit(self, record):
        logs_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": self.format(record),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        #Add exception info if present
        if record.exc_info:
            logs_entry["exception"] = {
                "type": str(record.exc_info[0].__name__),
                "message": str(record.exc_info[1]),
                "traceback": self.formatter.formatException(record.exc_info)
            }
        
        self.logs.append(logs_entry)

        #write to file
        with open(self.filename, 'w') as f:
            json.dump(self.logs, f, indent=2)

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.logger = logging.getLogger("shadow_clone_agent")
        self.logger.setLevel(logging.DEBUG)

        # prevent duplicate handlers
        if self.logger.handlers:
            return
        
        #Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(module)s:%(funcName)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        #JSON file handler
        json_handler = JSONFileHandler()
        json_handler.setLevel(logging.DEBUG)
        json_formatter = logging.Formatter('%(message)s')
        json_handler.setFormatter(json_formatter)

        #Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(json_handler)

    def debug(self, message:str):
        self.logger.debug(message)

    def info(self, message:str):
        self.logger.info(message)

    def warning(self, message:str):
        self.logger.warning(message)

    def error(self, message:str, exc_info=None):
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message:str, exc_info=None):
        self.logger.critical(message, exc_info=exc_info)


# Singleton instance
logger = Logger()

def get_logger():
    return logger