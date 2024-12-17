from functools import cache
from typing import Any, NewType, TypedDict

from mistune import BlockState, create_markdown
from mistune.renderers.markdown import MarkdownRenderer

Token = NewType("Token", dict[str, Any])


@cache
def get_parser():
    return create_markdown(renderer="ast")


def parse(markdown: str) -> list[Token]:
    return get_parser()(markdown)


@cache
def get_renderer():
    return MarkdownRenderer()


def unparse(tokens: list[Token]) -> str:
    return get_renderer()(tokens, BlockState())


class Chunk(TypedDict):
    breadcrumb: list[str]
    content: str


def extract_chunks(tokens: list[Token]) -> list[Chunk]:
    chunks: list[Chunk] = []

    heading_stack: list[str] = []
    buffered_tokens: list[Token] = []

    def flush():
        if buffered_tokens:
            chunks.append({"breadcrumb": heading_stack, "content": unparse(buffered_tokens).strip()})
            buffered_tokens.clear()

    for token in tokens:
        if token["type"] == "heading":
            flush()
            level: int = token["attrs"]["level"]
            title = unparse(token["children"]).strip()
            heading_stack = heading_stack[: level - 1] + [""] * (level - len(heading_stack) - 1) + [title]
        else:
            buffered_tokens.append(token)
    flush()

    return chunks


def split_markdown(markdown: str) -> list[Chunk]:
    return extract_chunks(parse(markdown))
