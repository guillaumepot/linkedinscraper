# src/utils/tools.py

"""Contains tools for the sources and scripts"""

import json
import time
import yaml


def ExecutionTime(function):
    """
    Decorator to measure the execution time of a function.

    Args:
        function: The function to measure the execution time of.

    Returns:
        The function with the execution time measured.
    """
    def timer(*args, **kwargs):
        start = time.time()
        results = function(*args, **kwargs)
        end = time.time()
        time_taken = end - start
        print(f"Execution time: {time_taken} seconds")
        return results
    
    return timer


def load_configuration(file_path: str, type: str = 'yaml'):
    """
    Load a configuration file.

    Args:
        file_path: The path to the configuration file.
        type: The type of the configuration file. (yaml or json)

    Returns:
        The configuration file.
    """
    if type == 'yaml':
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    elif type == 'json':
        with open(file_path, 'r') as f:
            return json.load(f)