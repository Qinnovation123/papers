from asyncio import sleep
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from niquests import AsyncSession, aput
from niquests.auth import BearerTokenAuth

from utils.config import env

session = AsyncSession(base_url="https://mineru.net/api/v4")
session.headers["Content-Type"] = "application/json"
session.auth = BearerTokenAuth(env.mineru_api_key)  # type: ignore


async def pdf_to_markdown(path: str | Path, polling_interval=0.5) -> str:
    """Convert local PDF to Markdown via MinerU API"""
    p = Path(path)
    assert p.is_file(), p

    # Step 1: Request upload URL
    upload_data = {"enable_formula": True, "language": "ch", "enable_table": True, "files": [{"name": p.name, "is_ocr": True}]}
    upload_res = await session.post("/file-urls/batch", json=upload_data)
    upload_res.raise_for_status()
    upload_result = upload_res.json()
    batch_id = upload_result["data"]["batch_id"]
    upload_url = upload_result["data"]["file_urls"][0]

    # Step 2: Upload the file
    with p.open("rb") as f:
        upload_file_res = await aput(upload_url, data=f)
    upload_file_res.raise_for_status()

    # Step 3: Poll for batch results
    while True:
        batch_res = await session.get(f"/extract-results/batch/{batch_id}")
        batch_res.raise_for_status()
        batch_data = batch_res.json()
        for result in batch_data["data"]["extract_result"]:
            if result["file_name"] == p.name:
                if result["state"] == "done":
                    zip_url = result["full_zip_url"]
                    # Download the zip file containing the parsed content
                    zip_res = await session.get(zip_url)
                    zip_res.raise_for_status()

                    # Process zip content directly in memory
                    zip_content = zip_res.content
                    assert zip_content is not None, zip_res

                    # Extract the zip file and find the markdown content
                    with ZipFile(BytesIO(zip_content), "r") as zip_ref:
                        for file_name in zip_ref.namelist():
                            if file_name.endswith(".md"):
                                return zip_ref.read(file_name).decode("utf-8")

                    error = f"Markdown file not found in zip: {zip_res}"

                elif result["state"] == "failed":
                    error = f"PDF parsing failed: {result['err_msg']}"

                else:
                    await sleep(polling_interval)
                    continue

                raise RuntimeError(error)
