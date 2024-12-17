from functools import cached_property
from io import StringIO

from attrs import define

from impl.chunk import Chunk, split_markdown
from impl.embed import embed
from impl.upsert import make_point, upsert


def render_chunk(chunk: Chunk):
    result = StringIO()
    for level, text in enumerate(chunk["breadcrumb"]):
        if text:
            result.write(f"{'#' * (level + 1)} {text}\n\n")
    result.write(chunk["content"])
    return result.getvalue()


@define
class Article:
    url: str
    title: str
    content: str

    @cached_property
    def chunks(self):
        return split_markdown(self.content)

    @property
    def queries(self):
        return list(map(render_chunk, self.chunks))

    async def get_embeddings(self):
        return await embed(self.queries)

    async def upsert(self):
        embeddings = await self.get_embeddings()

        points = [make_point(query, embedding, {"url": self.url, "title": self.title}) for query, embedding in zip(self.queries, embeddings)]

        await upsert(points)
