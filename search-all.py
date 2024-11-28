from asyncio import run

from impl.search import search
from impl.task import articles
from utils.rate_limit import IntervalLimiter


async def main():
    for i in articles:
        print(await search(i, rate_limiter))


rate_limiter = IntervalLimiter(5)


run(main())
