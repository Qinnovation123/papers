from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from routes.debug import router as debug_router

title, description = Path("README.md").read_text().split("\n", 1)

app = FastAPI(title=title.removeprefix("# "), version="dev", description=description)

app.include_router(debug_router)

app.get("/", include_in_schema=False)(lambda: RedirectResponse("/docs"))
