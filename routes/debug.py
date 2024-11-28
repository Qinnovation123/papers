from typing import Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Body, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import TypeAdapter, ValidationError

from impl.search import SearchResult, cache

router = APIRouter(tags=["Debug"])


def has_pdf_url(results: list[SearchResult]):
    return any(i["pdf_url"] for i in results)


def is_resolved(query: str):
    return query in cache and has_pdf_url(cache[query])  # type: ignore


@router.get("/tasks/{filter_by}")
async def tasks(filter_by: Literal["resolved-only", "all", "unresolved-only"]) -> list[str]:
    from impl.task import articles

    match filter_by:
        case "all":
            return articles
        case "resolved-only":
            return [i for i in articles if is_resolved(i)]
        case "unresolved-only":
            return [i for i in articles if not is_resolved(i)]


@router.get("/search/{query}")
async def search(query: str) -> list[SearchResult]:
    from impl.search import search

    return await search(query)  # type: ignore


@router.get("/pdf/fetch")
async def get_pdf(url: str, refresh: bool = False):
    from slugify import slugify

    from impl.pdf import fetch_pdf

    content = await fetch_pdf(url, refresh)

    auto_name = slugify(urlparse(url).path)

    return Response(content, media_type="application/pdf", headers={"content-disposition": f'attachment; filename="{auto_name}.pdf"'})


@router.post("/pdf/parse", response_model=str)
async def parse_pdf(data: bytes = Body(media_type="application/pdf")):
    from impl.pdf import extract_text

    return PlainTextResponse(await extract_text(data), media_type="text/markdown")


@router.get("/pdf")
async def fetch_and_parse(url: str):
    from impl.pdf import get_markdown

    return PlainTextResponse(await get_markdown(url), media_type="text/markdown")


@router.get("/cache", response_model=dict[str, list[SearchResult]])
def get_cache():
    return JSONResponse({i: cache[i] for i in cache}, headers={"content-disposition": 'attachment; filename="cache.json"'})


@router.put("/cache")
def update_cache(body: bytes = Body(media_type="application/pdf")):
    try:
        data = TypeAdapter(dict[str, list[SearchResult]]).validate_json(body)
    except ValidationError as e:
        raise RequestValidationError(e.errors())

    from alive_progress import alive_it

    for i, j in alive_it(data.items(), len(data), title=" syncing cache"):
        cache[i] = j
