from contextlib import AbstractAsyncContextManager
from typing import TypedDict

from diskcache import Cache
from parsel import Selector

from utils.config import env
from utils.http import fetch


class SearchResult(TypedDict):
    query: str
    gs_title: str
    page_url: str
    pdf_url: str | None


class BlockedError(Exception):
    pass


async def _search(query: str):
    html = await fetch("https://scholar.google.com/scholar", {"q": query})

    document = Selector(html)

    if document.css("#gs_captcha_f"):
        raise BlockedError

    results: list[SearchResult] = []

    for item in document.css(".gs_or"):
        page_anchor = item.css("h3 a")
        if not page_anchor:
            continue
        page_link = page_anchor.attrib["href"]

        title = page_anchor.css("::text").get()
        assert title, page_anchor

        pdf_link = None

        if pdf_anchor := item.css(".gs_or_ggsm a"):
            pdf_description = pdf_anchor.get()
            assert pdf_description, pdf_anchor
            if "[PDF]" in pdf_description:
                pdf_link = pdf_anchor.attrib["href"]
            else:
                print(pdf_description)

        results.append({
            "query": query,
            "gs_title": title,
            "page_url": page_link,
            "pdf_url": pdf_link,
        })

    return results


cache = Cache[str, list[SearchResult]](env.storage_dir / "cache" / "search")


async def search(query: str, lock: AbstractAsyncContextManager | None = None):
    if query in cache:
        return cache[query]
    if lock:
        async with lock:
            result = await _search(query)
    else:
        result = await _search(query)
    cache.set(query, result)
    return result
