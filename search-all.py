from asyncio import TaskGroup, run

from impl.task import Article, articles
from utils.rate_limit import IntervalLimiter

total = 0
success = 0


async def on_article(article: Article):
    global total, success

    info = await article.get_info(rate_limiter)

    total += 1
    if info.pdf_url:
        print("|", end="", flush=True)
        success += 1
    else:
        print(end=" ")


async def main():
    async with TaskGroup() as tg:
        for i in articles:
            tg.create_task(on_article(i))


rate_limiter = IntervalLimiter(5)


run(main())


print(f"Total: {total}, Success: {success}")
