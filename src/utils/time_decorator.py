# src/utils/time_decorator.py

import time

def ExecutionTime(function):
    """
    Returns execution time of a function
    """
    def timer(*args, **kwargs):
        start = time.time()
        results = function(*args, **kwargs)
        end = time.time()
        time_taken = end - start
        print(f"Execution time: {time_taken} seconds")
        return results
    
    return timer