from asyncio import Lock, TaskGroup
from collections import Counter
from contextlib import suppress
from typing import Literal, cast

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from impl.article import Article
from impl.pdf import extract_text, fetch_pdf
from impl.search import SearchResult, cache
from impl.task import articles
from utils.concurrency import throttle

lock = Lock()


State = Literal[0, 1, 2, 3, 4]


class Job:
    def __init__(self, url: str):
        self.url = url
        self.state: State = 0

    @throttle(20)
    async def download(self, url: str):
        return await fetch_pdf(url)

    @throttle(50)
    async def extract(self, pdf: bytes):
        return await extract_text(pdf)

    @throttle(30)
    async def embed_and_upsert(self, markdown: str):
        article = Article(url=self.url, title="", content=markdown)
        await article.upsert()

    async def run(self, url: str):
        with suppress(Exception):
            pdf = await self.download(url)
            self.state = 1
            markdown = await self.extract(pdf)
            self.state = 2
            await self.embed_and_upsert(markdown)
            self.state = 3


class Batch:
    def __init__(self, urls: list[str]):
        self.urls = urls
        self.jobs: list[Job] = []

    async def start(self):
        global current_batch

        async with TaskGroup() as tg:
            for url in self.urls:
                self.jobs.append(job := Job(url))
                tg.create_task(job.run(url))

        current_batch = None

    @property
    def info(self):
        return Counter(job.state for job in self.jobs)


router = APIRouter(tags=["Job"])


current_batch: Batch | None = None


@router.put("/batch")
async def run_all(bg: BackgroundTasks) -> dict[Literal["total"], int]:
    global current_batch
    if current_batch:
        raise HTTPException(400, "A batch is already running")
    urls = [result["pdf_url"] for i in articles for result in cast(list[SearchResult], cache.get(i, [])) if result["pdf_url"]]
    current_batch = Batch(urls)
    bg.add_task(current_batch.start)
    return {"total": len(urls)}


class BatchInfo(BaseModel):
    total: int
    info: dict[State, int]


@router.get("/batch")
async def job_info():
    if current_batch:
        return BatchInfo(total=len(current_batch.jobs), info=current_batch.info)  # type: ignore
