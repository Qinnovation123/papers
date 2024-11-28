from pydantic_settings import BaseSettings


class Config(BaseSettings):
    jina_api_key: str

    proxy_base_url: str = "https://http-proxy.up.railway.app"
    pdf2md_base_url: str = "https://pdf2md.up.railway.app"

    model_config = {"env_file": ".env"}


env = Config()  # type: ignore
