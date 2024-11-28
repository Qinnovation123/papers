from asyncio import Lock, sleep
from time import perf_counter


class IntervalLimiter:
    def __init__(self, interval: float):
        self._interval = interval
        self._lock = Lock()
        self._last = -interval

    async def __aenter__(self):
        await self._lock.acquire()
        now = perf_counter()
        wait_time = self._interval - (now - self._last)
        if wait_time > 0:
            await sleep(wait_time)
        self._last = perf_counter()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self._lock.release()
