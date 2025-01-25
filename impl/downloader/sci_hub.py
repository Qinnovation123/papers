from asyncio import Semaphore
from urllib.parse import urljoin

from parsel import Selector

from utils.config import env
from utils.http import fetch

BASE_URL = env.scihub_base_url


sem = Semaphore(50)


async def get_download_url(doi: str):
    url = urljoin(BASE_URL, doi)
    async with sem:
        html = await fetch(url)
    attributes = Selector(html).css("embed").attrib
    if attributes.get("id") == "pdf":
        return attributes["src"]
