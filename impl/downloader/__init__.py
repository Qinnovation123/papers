from .sci_hub import get_download_url
from .wos import wos_to_doi


async def fetch_wos(unique_id: str):
    doi = await wos_to_doi(unique_id)
    if doi is None:
        return None, None
    url = await get_download_url(doi)
    return doi, url
