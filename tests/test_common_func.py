# tests/test_common_func.py


import pytest
import json
import yaml
import tempfile
import os
import time

from src.utils.common_func import ExecutionTime, load_configuration


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
    
    def test_execution_time_decorator_with_no_arguments(self):
        """
        Test ExecutionTime decorator works with functions that take no arguments
        """
        @ExecutionTime
        def no_args_function():
            return "success"
        
        result = no_args_function()
        assert result == "success"
    
    def test_execution_time_decorator_with_keyword_arguments(self):
        """
        Test ExecutionTime decorator works with functions using keyword arguments
        """
        @ExecutionTime
        def keyword_function(name, age=25):
            return f"{name} is {age} years old"
        
        result = keyword_function("Alice", age=30)
        assert result == "Alice is 30 years old"
    
    def test_execution_time_decorator_with_complex_return_types(self):
        """
        Test ExecutionTime decorator works with functions returning complex data types
        """
        @ExecutionTime
        def complex_return_function():
            return {
                "list": [1, 2, 3],
                "dict": {"key": "value"},
                "tuple": (1, 2, 3)
            }
        
        result = complex_return_function()
        expected = {
            "list": [1, 2, 3],
            "dict": {"key": "value"},
            "tuple": (1, 2, 3)
        }
        assert result == expected
    
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
    
    def test_execution_time_decorator_with_exception_handling(self):
        """
        Test ExecutionTime decorator behavior when decorated function raises an exception
        """
        @ExecutionTime
        def failing_function():
            raise ValueError("Test exception")
        
        with pytest.raises(ValueError, match="Test exception"):
            failing_function()


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
    
    def test_load_yaml_configuration_defaults_to_yaml_type(self):
        """
        Test that load_configuration defaults to YAML when no type is specified
        """
        yaml_data = {"default": "yaml", "test": True}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_data, f)
            temp_file_path = f.name
        
        try:
            # Test without specifying type parameter
            result = load_configuration(temp_file_path)
            assert result == yaml_data
        finally:
            os.unlink(temp_file_path)
    
    def test_load_configuration_file_not_found_raises_exception(self):
        """
        Test that load_configuration raises FileNotFoundError for non-existent files
        """
        non_existent_file = "/path/to/non/existent/file.yaml"
        
        with pytest.raises(FileNotFoundError):
            load_configuration(non_existent_file, type='yaml')
    
    def test_load_malformed_yaml_configuration_raises_exception(self):
        """
        Test that load_configuration raises exception for malformed YAML files
        """
        # Create truly malformed YAML that will cause a parsing error
        malformed_yaml_content = """
        invalid_yaml: [
        unclosed_bracket: "value"
        - item1
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(malformed_yaml_content)
            temp_file_path = f.name
        
        try:
            with pytest.raises(yaml.YAMLError):
                load_configuration(temp_file_path, type='yaml')
        finally:
            os.unlink(temp_file_path)
    
    def test_load_malformed_json_configuration_raises_exception(self):
        """
        Test that load_configuration raises exception for malformed JSON files
        """
        malformed_json_content = '{"key": "value", "incomplete":'  # Missing closing
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(malformed_json_content)
            temp_file_path = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_configuration(temp_file_path, type='json')
        finally:
            os.unlink(temp_file_path)
    
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
    
    def test_load_configuration_with_complex_nested_structure(self):
        """
        Test load_configuration with complex nested data structures
        """
        complex_data = {
            "application": {
                "name": "LinkedInScraper",
                "version": "1.0.0",
                "environments": {
                    "development": {
                        "debug": True,
                        "database_url": "sqlite:///dev.db",
                        "features": ["logging", "debugging"]
                    },
                    "production": {
                        "debug": False,
                        "database_url": "postgresql://prod_server/db",
                        "features": ["logging", "monitoring", "caching"]
                    }
                },
                "constants": {
                    "max_retries": 5,
                    "timeout_seconds": 30.5,
                    "enabled": True
                }
            }
        }
        
        # Test with YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(complex_data, f)
            yaml_file_path = f.name
        
        # Test with JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(complex_data, f)
            json_file_path = f.name
        
        try:
            yaml_result = load_configuration(yaml_file_path, type='yaml')
            json_result = load_configuration(json_file_path, type='json')
            
            assert yaml_result == complex_data
            assert json_result == complex_data
            assert yaml_result == json_result
        finally:
            os.unlink(yaml_file_path)
            os.unlink(json_file_path)
    
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


class TestIntegrationScenarios:
    """Integration tests combining multiple functions"""
    
    def test_execution_time_decorator_with_load_configuration(self, capsys):
        """
        Test ExecutionTime decorator applied to load_configuration function
        """
        @ExecutionTime
        def timed_load_config(file_path, file_type):
            return load_configuration(file_path, type=file_type)
        
        test_data = {"integration": "test", "success": True}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_data, f)
            temp_file_path = f.name
        
        try:
            result = timed_load_config(temp_file_path, 'yaml')
            captured = capsys.readouterr()
            
            assert result == test_data
            assert "Execution time:" in captured.out
        finally:
            os.unlink(temp_file_path)


# Test fixtures for reusable test data
@pytest.fixture
def sample_yaml_config():
    """Fixture providing sample YAML configuration data"""
    return {
        "scraper": {
            "delay_seconds": 2,
            "max_profiles": 100,
            "output_format": "json"
        },
        "linkedin": {
            "base_url": "https://linkedin.com",
            "search_endpoints": [
                "/search/results/people/",
                "/search/results/companies/"
            ]
        }
    }

@pytest.fixture
def sample_json_config():
    """Fixture providing sample JSON configuration data"""
    return {
        "api": {
            "version": "v1",
            "rate_limit": 1000,
            "authentication": {
                "type": "oauth2",
                "scopes": ["read", "write"]
            }
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "handlers": ["console", "file"]
        }
    }


class TestWithFixtures:
    """Tests using pytest fixtures for better test organization"""
    
    def test_load_configuration_with_sample_yaml_fixture(self, sample_yaml_config):
        """
        Test load_configuration using the sample YAML fixture
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_yaml_config, f)
            temp_file_path = f.name
        
        try:
            result = load_configuration(temp_file_path, type='yaml')
            assert result == sample_yaml_config
            assert result["scraper"]["delay_seconds"] == 2
            assert len(result["linkedin"]["search_endpoints"]) == 2
        finally:
            os.unlink(temp_file_path)
    
    def test_load_configuration_with_sample_json_fixture(self, sample_json_config):
        """
        Test load_configuration using the sample JSON fixture
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_json_config, f)
            temp_file_path = f.name
        
        try:
            result = load_configuration(temp_file_path, type='json')
            assert result == sample_json_config
            assert result["api"]["rate_limit"] == 1000
            assert result["logging"]["level"] == "INFO"
        finally:
            os.unlink(temp_file_path) 