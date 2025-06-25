# tests/test_common_func.py


import pytest
import json
import yaml
import tempfile
import os
import time

from src.utils.tools import ExecutionTime, load_configuration


class TestExecutionTimeDecorator:
    """Test suite for the ExecutionTime decorator"""
    
    def test_execution_time_decorator_returns_correct_result(self):
        """
        Test that ExecutionTime decorator returns the correct result from decorated function
        """
        @ExecutionTime
        def sample_function(a, b):
            return a + b
        
        result = sample_function(3, 5)
        assert result == 8
    
    def test_execution_time_decorator_prints_timing_information(self, capsys):
        """
        Test that ExecutionTime decorator prints execution time information
        """
        @ExecutionTime
        def timed_function():
            time.sleep(0.01)  # Small delay to ensure measurable time
            return "completed"
        
        result = timed_function()
        captured = capsys.readouterr()
        
        assert result == "completed"
        assert "Execution time:" in captured.out
        assert "seconds" in captured.out
    

class TestLoadConfigurationFunction:
    """Test suite for the load_configuration function"""
    
    def test_load_yaml_configuration_successfully(self):
        """
        Test successful loading of a valid YAML configuration file
        """
        yaml_data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "testdb"
            },
            "api": {
                "timeout": 30,
                "retries": 3
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_data, f)
            temp_file_path = f.name
        
        try:
            result = load_configuration(temp_file_path, type='yaml')
            assert result == yaml_data
        finally:
            os.unlink(temp_file_path)
    

    def test_load_json_configuration_successfully(self):
        """
        Test successful loading of a valid JSON configuration file
        """
        json_data = {
            "server": {
                "host": "127.0.0.1",
                "port": 8080
            },
            "features": {
                "logging": True,
                "caching": False
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            temp_file_path = f.name
        
        try:
            result = load_configuration(temp_file_path, type='json')
            assert result == json_data
        finally:
            os.unlink(temp_file_path)
    

    def test_load_configuration_file_not_found_raises_exception(self):
        """
        Test that load_configuration raises FileNotFoundError for non-existent files
        """
        non_existent_file = "/path/to/non/existent/file.yaml"
        
        with pytest.raises(FileNotFoundError):
            load_configuration(non_existent_file, type='yaml')
    

    def test_load_empty_yaml_configuration_returns_none(self):
        """
        Test that load_configuration handles empty YAML files correctly
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")  # Empty file
            temp_file_path = f.name
        
        try:
            result = load_configuration(temp_file_path, type='yaml')
            assert result is None
        finally:
            os.unlink(temp_file_path)
    

    def test_load_empty_json_configuration_raises_exception(self):
        """
        Test that load_configuration raises exception for empty JSON files
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("")  # Empty file
            temp_file_path = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_configuration(temp_file_path, type='json')
        finally:
            os.unlink(temp_file_path)
    

    def test_load_configuration_with_unsupported_type_returns_none(self):
        """
        Test that load_configuration returns None for unsupported file types
        """
        yaml_data = {"fallback": "test", "works": True}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_data, f)
            temp_file_path = f.name
        
        try:
            # Test with unsupported type
            result = load_configuration(temp_file_path, type='unsupported')
            assert result is None
        finally:
            os.unlink(temp_file_path)