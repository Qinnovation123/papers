from urllib.parse import urljoin

from utils.config import env
from utils.http import session, ua
from utils.rate_limit import IntervalLimiter

SID = env.wos_sid
BASE_URL = env.wos_base_url


sem = IntervalLimiter(1)


async def wos_to_doi(unique_id: str) -> str | None:
    url = urljoin(BASE_URL, f"/api/wosnx/core/getFullRecordByQueryId?{SID=!s}")

    payload = {
        "id": {"value": unique_id, "type": "colluid"},
        "retrieve": {"first": 1},
        "product": "ALLDB",
        "searchMode": "general",
        "serviceMode": "summary",
        "viewType": "records",
    }

    async with sem:
        with await session.post(url, headers={"user-agent": ua.random, "accept": "application/json"}, json=payload) as res:
            data, *_ = res.json()

    if data["key"] == "error":
        print(f" {data['payload']} ", end="")
        return

    if "doi" in data["payload"]:
        return data["payload"]["doi"]
