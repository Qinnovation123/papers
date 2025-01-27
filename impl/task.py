from contextlib import AbstractAsyncContextManager, suppress
from csv import DictReader
from functools import cache
from hashlib import md5
from json import dumps
from pathlib import Path

from attrs import define, field

from impl.downloader import fetch_wos, get_download_url
from impl.search import SearchResult, search
from utils.clsprop import classproperty


@define
class DownloadInfo:
    metadata: dict[str, str] = field(repr=False)
    pdf_url: str | None = None
    doi: str | None = None
    search_results: list[SearchResult] | None = field(default=None, repr=False)


@define
class Article:
    metadata: dict

    @property
    def title(self) -> str:
        return self.metadata["Article Title"]

    @property
    def unique_id(self) -> str:
        return self.metadata["UT (Unique ID)"]

    @property
    def doi(self) -> str:
        return self.metadata["DOI"]

    @classproperty
    @cache
    @staticmethod
    def cache():
        from diskcache import Cache

        path = Path("data/cache/article-info")
        path.mkdir(parents=True, exist_ok=True)
        return Cache[str, DownloadInfo](path)

    @property
    def key(self):
        if self.unique_id:
            return self.unique_id
        elif self.doi:
            return f"DOI:{self.doi}"
        else:
            return f"MD5:{md5(dumps(self.metadata, sort_keys=True).encode()).hexdigest()}"

    async def get_info(self, lock: AbstractAsyncContextManager) -> DownloadInfo:
        with suppress(KeyError):
            return self.cache[self.key]

        info = DownloadInfo(self.metadata, self.doi or None)
        if self.doi:
            info.pdf_url = await get_download_url(self.doi)
        elif self.unique_id.startswith("WOS:"):
            info.doi, info.pdf_url = await fetch_wos(self.unique_id)
        else:
            info.search_results = await search(self.title, lock)
            for res in info.search_results:
                if url := res["pdf_url"]:
                    info.pdf_url = url

        if info.pdf_url:
            self.cache[self.key] = info

        return info


with Path("data/secondary-metabolism.csv").open(encoding="utf-8") as f:
    articles = list(map(Article, DictReader(f)))
    titles = [i.title for i in articles]


__all__ = ["articles", "titles"]
