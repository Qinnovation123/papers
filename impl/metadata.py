from asyncio import Semaphore
from traceback import print_exc
from typing import TypedDict

from diskcache import Cache

from impl.pdf import extract_metadata, fetch_pdf
from impl.task import Article
from utils.config import env


class Metadata(TypedDict):
    title: str
    abstract: str
    keywords: list[str]


path = env.storage_dir / "cache" / "article-metadata"
path.mkdir(parents=True, exist_ok=True)
cache = Cache[str, Metadata](path)

sem = Semaphore(5)


async def get_metadata(article: Article) -> Metadata | None:
    if article.unique_id in cache:
        return cache[article.unique_id]

    try:
        info = await article.get_info(sem)
        if url := info.pdf_url:
            if url.startswith("//"):
                url = f"https:{url}"
            elif url.startswith("/"):  # TODO: fix these relative urls
                return
            content = await fetch_pdf(url)
            metadata: Metadata = await extract_metadata(content)  # type: ignore
            if metadata.pop("success"):
                cache[article.unique_id] = metadata
                return metadata

    except Exception:
        print_exc()
