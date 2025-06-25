# tests/test_logger_manager.py

import pytest
import logging
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.utils.LoggerManager import LoggerManager


class TestLoggerManager:
    """Test cases for LoggerManager class"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.test_logger_config = {
            "logging": {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    }
                },
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "formatter": "default",
                        "level": "INFO"
                    },
                    "file": {
                        "class": "logging.FileHandler",
                        "formatter": "default",
                        "filename": "/tmp/test.log",
                        "level": "DEBUG"
                    }
                },
                "loggers": {
                    "default": {
                        "level": "INFO",
                        "handlers": ["console", "file"],
                        "propagate": False
                    },
                    "test": {
                        "level": "DEBUG",
                        "handlers": ["console", "file"],
                        "propagate": False
                    }
                }
            }
        }

    def test_configure_logger_default_name_success(self):
        """Test successful logger configuration with default name"""
        with patch('logging.config.dictConfig') as mock_dict_config:
            with patch('logging.getLogger') as mock_get_logger:
                with patch('os.makedirs') as mock_makedirs:
                    mock_logger = MagicMock()
                    mock_get_logger.return_value = mock_logger
                    
                    result = LoggerManager.configure_logger(
                        name = "default", 
                        logger_config = self.test_logger_config
                    )
                    
                    # Verify directory creation
                    mock_makedirs.assert_called_once_with('/tmp', exist_ok = True)
                    
                    # Verify logging configuration
                    mock_dict_config.assert_called_once_with(self.test_logger_config["logging"])
                    
                    # Verify logger retrieval and configuration
                    mock_get_logger.assert_called_once_with("default")
                                        
                    assert result == mock_logger

    def test_configure_logger_custom_name_success(self):
        """Test successful logger configuration with custom name"""
        with patch('logging.config.dictConfig'):
            with patch('logging.getLogger') as mock_get_logger:
                with patch('os.makedirs'):
                    mock_logger = MagicMock()
                    mock_get_logger.return_value = mock_logger
                    
                    result = LoggerManager.configure_logger(
                        name=  "test", 
                        logger_config = self.test_logger_config
                    )
                    
                    mock_get_logger.assert_called_once_with("test")
                    assert result == mock_logger

    def test_configure_logger_invalid_name_raises_error(self):
        """Test that configuring logger with invalid name raises ValueError"""
        with pytest.raises(ValueError, match="Logger invalid_logger not found in logging config file"):
            LoggerManager.configure_logger(
                name = "invalid_logger", 
                logger_config = self.test_logger_config
            )

    def test_configure_logger_directory_creation(self):
        """Test that log directory is created properly"""
        with patch('logging.config.dictConfig'):
            with patch('logging.getLogger') as mock_get_logger:
                with patch('os.makedirs') as mock_makedirs:
                    mock_logger = MagicMock()
                    mock_get_logger.return_value = mock_logger
                    
                    LoggerManager.configure_logger(
                        name = "default", 
                        logger_config = self.test_logger_config
                    )
                    
                    # Verify makedirs is called with correct path and exist_ok=True
                    mock_makedirs.assert_called_once_with('/tmp', exist_ok=True)

    def test_configure_logger_integration(self):
        """Integration test with real logging configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test config with temporary directory
            test_config = {
                "logging": {
                    "version": 1,
                    "formatters": {
                        "simple": {"format": "%(levelname)s - %(message)s"}
                    },
                    "handlers": {
                        "file": {
                            "class": "logging.FileHandler",
                            "formatter": "simple",
                            "filename": os.path.join(temp_dir, "test.log")
                        }
                    },
                    "loggers": {
                        "integration_test": {
                            "level": "DEBUG",
                            "handlers": ["file"],
                            "propagate": False
                        }
                    }
                }
            }
            
            logger = LoggerManager.configure_logger(
                name="integration_test",
                logger_config = test_config
            )
            
            # Test that logger works
            assert logger.name == "integration_test"
            assert logger.level == logging.DEBUG
            
            # Test logging functionality
            logger.info("Test message")
            log_file = os.path.join(temp_dir, "test.log")
            assert os.path.exists(log_file)
            
            with open(log_file, 'r') as f:
                log_content = f.read()
                assert "Test message" in log_content 