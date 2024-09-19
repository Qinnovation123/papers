from fake_useragent import FakeUserAgent
from niquests import AsyncSession

ua = FakeUserAgent(platforms=["pc"])  # Google Scholar will return PDF links if the user-agent is a PC

session = AsyncSession(happy_eyeballs=True)


async def fetch(url: str, params={}):
    with await session.get(url, params=params, headers={"user-agent": ua.random}) as res:
        return res.text


__all__ = ["fetch"]
