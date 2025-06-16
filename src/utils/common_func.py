# src/utils/commun_func.py

import json
import time
import yaml


def ExecutionTime(function):
    def timer(*args, **kwargs):
        start = time.time()
        results = function(*args, **kwargs)
        end = time.time()
        time_taken = end - start
        print(f"Execution time: {time_taken} seconds")
        return results
    
    return timer

def load_configuration(file_path: str, type: str = 'yaml'):
    if type == 'yaml':
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    elif type == 'json':
        with open(file_path, 'r') as f:
            return json.load(f)