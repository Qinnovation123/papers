from asyncio import Semaphore
from os import getenv

from utils.http import session, ua

proxy_base_url = getenv("PROXY_BASE_URL", "https://http-proxy.up.railway.app")


async def fetch_pdf(url: str):
    headers = {"user-agent": ua.random, "accept": "application/pdf"}

    res = await session.get(f"{proxy_base_url}/proxy?url={url}", headers=headers)
    res.raise_for_status()
    assert res.content is not None, res
    return res.content


pdf2md_base_url = getenv("PDF2MD_BASE_URL", "https://pdf2md.up.railway.app")


async def extract_text(raw: bytes):
    res = await session.post(f"{pdf2md_base_url}/convert", data=raw, headers={"content-type": "application/pdf"})
    res.raise_for_status()
    assert res.text is not None, res
    return res.text


sem = Semaphore(20)


async def get_markdown(url: str):
    async with sem:
        pdf = await fetch_pdf(url)
    return await extract_text(pdf)
