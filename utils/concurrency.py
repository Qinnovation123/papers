from asyncio import Semaphore
from collections.abc import Awaitable, Callable
from functools import wraps


def throttle(max_concurrency: int):
    sem = Semaphore(max_concurrency)

    def decorator[**P, T](func: Callable[P, Awaitable[T]]):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            async with sem:
                return await func(*args, **kwargs)

        return wrapper

    return decorator
