from asyncio import Semaphore

from utils.config import env
from utils.http import session, ua


async def fetch_pdf(url: str, refresh=False):
    headers = {"user-agent": ua.random, "accept": "application/pdf"}

    params = {"url": url}
    if refresh:
        params["refresh"] = "true"

    res = await session.get(f"{env.proxy_base_url}/proxy", headers=headers, params=params)
    res.raise_for_status()
    assert res.content is not None, res
    return res.content


async def extract_text(raw: bytes):
    res = await session.post(f"{env.pdf2md_base_url}/convert", data=raw, headers={"content-type": "application/pdf"})
    res.raise_for_status()
    assert res.text is not None, res
    return res.text


sem = Semaphore(20)


async def get_markdown(url: str):
    async with sem:
        pdf = await fetch_pdf(url)
    return await extract_text(pdf)
