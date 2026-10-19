import time
import logging
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

log = logging.getLogger("findex")

P = ParamSpec("P")
R = TypeVar("R")

def timed(fn: Callable[P, R]) -> Callable[P, R]:
    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        t0 = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - t0
            log.debug("%s took %.2f ms", fn.__name__, elapsed * 1000)
    return wrapper