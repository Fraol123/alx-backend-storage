#!/usr/bin/env python3
"""python module to interact with redis server"""
import redis
import uuid
from typing import Union, Optional, Callable
from functools import wraps


def call_history(method: Callable) -> Callable:
    """decorator function to recode parameter & output history"""
    key = method.__qualname__
    inputs = key + ":inputs"
    outputs = key + ":outputs"

    @wraps(method)
    def wrapper(self, *args, **kwds):
        """wrapped function"""
        self._redis.rpush(inputs, str(args))
        data = method(self, *args, **kwds)
        self._redis.rpush(outputs, str(data))
        return data
    return wrapper


def count_calls(method: Callable) -> Callable:
    """decorator function"""
    key = method.__qualname__

    @wraps(method)
    def wrapper(self, *args, **kwds):
        """method wrapper"""
        self._redis.incr(key)
        return method(self, *args, **kwds)

    return wrapper


class Cache:
    """class to store Redis client information"""

    def __init__(self):
        """ iniitalize Redis DB """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """ create a random key & stores it with data """
        key: uuid.UUID = uuid.uuid1()
        self._redis.set(str(key), data)
        return str(key)

    def get(self, key: str, fn: Optional[Callable]
            = None) -> Union[str, bytes, int, float]:
        """convert the data back to the desired format"""
        data = self._redis.get(key)
        if fn:
            data = fn(data)
        return data

    def get_str(self, data: bytes) -> str:
        """convert data to string"""
        return str(data, 'UTF-8')

    def get_int(self, data: bytes) -> int:
        """convert data to init"""
        return int.from_bytes(data, "big")


def replay(method: Callable):
    """ display the history of calls for a function """
    key = method.__qualname__
    inputs = key + ":inputs"
    outputs = key + ":outputs"
    redis = method.__self__._redis
    count = redis.get(key).decode("utf-8")
    print("{} was called {} times:".format(key, count))
    inputList = redis.lrange(inputs, 0, -1)
    outputList = redis.lrange(outputs, 0, -1)
    redis_all = list(zip(inputList, outputList))
    for a, b in redis_all:
        attr, data = a.decode("utf-8"), b.decode("utf-8")
        print("{}(*{}) -> {}".format(key, attr, data))
