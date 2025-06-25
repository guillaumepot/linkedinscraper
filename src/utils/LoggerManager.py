# src/class/LoggerManager.py

"""
A simple class to create a logger for the application.

Usage:
from src.class.LoggerManager import LoggerManager

logger = LoggerManager.configure_logger(name = "ElasticsearchEngine")
logger.info("Hello, world!")
"""

import logging
import logging.config
import os
from pathlib import Path
from src.utils.tools import load_configuration

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.json"

LOGGER_CONFIG = load_configuration(file_path=str(CONFIG_PATH), type='json')['Logger']

class LoggerManager:
    @staticmethod
    def configure_logger(name:str =' default', logger_config:dict = LOGGER_CONFIG) -> logging.Logger:

        if name not in logger_config["logging"]["loggers"]:
            raise ValueError(f"Logger {name} not found in logging config file")
        else:
            log_directory = os.path.dirname(logger_config["logging"]["handlers"]["file"]["filename"])
            os.makedirs(log_directory, exist_ok=True)
            logging.config.dictConfig(logger_config["logging"])

            logger = logging.getLogger(name)
            
            return logger