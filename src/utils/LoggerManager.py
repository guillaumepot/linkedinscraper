# src/utils/LoggerManager.py
# Code: v1.0.0
# Doc: https://docs.python.org/3/library/logging.html#module-logging

import logging
import logging.config
import os
import yaml

current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'logger_config.yaml')
with open(config_path, 'r') as f:
    LOGGER_CONFIG = yaml.safe_load(f)

class LoggerManager:
    @staticmethod
    def configure_logger(name:str =' default', logger_config:dict = LOGGER_CONFIG, verbose: bool = False) -> logging.Logger:

        if name not in logger_config["logging"]["loggers"]:
            raise ValueError(f"Logger {name} not found in logging config file")
        else:
            log_directory = os.path.dirname(logger_config["logging"]["handlers"]["file"]["filename"])
            os.makedirs(log_directory, exist_ok=True)
            logging.config.dictConfig(logger_config["logging"])

            logger = logging.getLogger(name)

            level = logging.DEBUG if verbose else logging.INFO
            
            logger.setLevel(level)

            return logger