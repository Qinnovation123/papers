from base64 import b64decode
from functools import partial
from operator import itemgetter
from os import getenv

import numpy as np
from niquests.auth import BearerTokenAuth

from utils.http import session

api_key = getenv("JINA_API_KEY")
assert api_key, "JINA_API_KEY is required"

auth = BearerTokenAuth(api_key)
headers = {"Content-Type": "application/json"}

post = partial(session.post, headers=headers, auth=auth)

options = {
    "model": "jina-embeddings-v3",
    "task": "text-matching",
    "embedding_type": "base64",
    "dimensions": 1024,
}


async def embed(queries: list[str]):
    res = await post("https://api.jina.ai/v1/embeddings", json={"input": queries, **options})

    data = res.json()

    embeddings = sorted(data["data"], key=itemgetter("index"))

    return [base64_to_float(item["embedding"]) for item in embeddings]


def base64_to_float(data: str):
    array = np.frombuffer(b64decode(data), dtype=np.float32)
    assert array.shape == (1024,), array.shape
    return array
