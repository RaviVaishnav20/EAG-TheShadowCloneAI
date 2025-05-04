from typing import Dict, Any, Type, TypeVar, Optional
import threading

T = TypeVar('T')

class Singleton:
    """
    A decorator class to implement the Singleton pattern.

    Usage:
        @Singleton
        class MyClass:
            pass
    """
    _instances: Dict[Type, Any] = {}
    _lock = threading.Lock()

    def __init__(self, cls):
        self._cls = cls

    def __call__(self, *args: Any, **kwargs: Any):
        with self._lock:
            if self._cls not in self._instances:
                instance = self._cls(*args, **kwargs)
                self._instances[self._cls] = instance
        return self._instances[self._cls]
    
