from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING, Any

from utils.config import env

if TYPE_CHECKING:
    from qdrant_client.models import CollectionInfo, PointStruct


@cache
def get_client():
    from qdrant_client import AsyncQdrantClient

    return AsyncQdrantClient(env.qdrant_url, api_key=env.qdrant_api_key)


async def create_collection():
    from qdrant_client.models import Distance, VectorParams

    await get_client().create_collection(env.qdrant_collection_name, VectorParams(size=1024, distance=Distance.DOT))


async def get_collection() -> CollectionInfo:
    from qdrant_client.http.exceptions import UnexpectedResponse

    try:
        return await get_client().get_collection(env.qdrant_collection_name)
    except ValueError as err:
        if err.args == (f"Collection {env.qdrant_collection_name} not found",):
            # in-memory collection
            await create_collection()
            return await get_collection()
        else:
            print(err)
            raise
    except UnexpectedResponse as err:
        print(err)
        if err.status_code == 502:
            # server not awake yet
            return await get_collection()
        if err.status_code == 404:
            await create_collection()
            return await get_collection()
        raise


async def ensure_collection():
    collection = await get_collection()
    assert collection.status == "green", collection.status


def get_id(content: str):
    from hashlib import md5

    return md5(content.encode()).hexdigest()


def make_point(query: str, embedding: list[float], metadata: dict[str, Any]):
    from qdrant_client.models import PointStruct

    return PointStruct(id=get_id(query), vector=embedding, payload=metadata)


async def upsert(points: list[PointStruct], wait=True):
    await ensure_collection()
    await get_client().upsert(env.qdrant_collection_name, points, wait=wait)
