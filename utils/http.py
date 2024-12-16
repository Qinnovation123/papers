from fake_useragent import FakeUserAgent
from niquests import AsyncSession

ua = FakeUserAgent(platforms=["desktop"])  # Google Scholar will return PDF links if the user-agent is a desktop browser

session = AsyncSession()


async def fetch(url: str, params=None):
    with await session.get(url, params=params, headers={"user-agent": ua.random}) as res:
        return res.text


__all__ = ["fetch"]
