from functools import wraps

def atomic(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return wrapper
    return wrapper
