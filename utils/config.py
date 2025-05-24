from pathlib import Path

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    jina_api_key: str = ""
    mineru_api_key: str = ""

    qdrant_url: str = ":memory:"
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "papers"
    proxy_base_url: str = "https://http-proxy.up.railway.app"
    pdf2md_base_url: str = "https://pdf2md.up.railway.app"

    wos_base_url: str = "https://www.webofscience.com/"
    wos_sid: str = ""

    scihub_base_url: str = "https://www.wellesu.com/"

    storage_dir: Path = Path(__file__, "../../data").resolve().relative_to(Path.cwd())

    model_config = {"env_file": ".env", "extra": "allow"}


env = Config()  # type: ignore
