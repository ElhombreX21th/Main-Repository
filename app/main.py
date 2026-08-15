from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import audit, auth, expenses, integrations, policies, privacy, reports, users
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
for router in (
    auth.router,
    users.router,
    expenses.router,
    policies.router,
    reports.router,
    integrations.router,
    privacy.router,
    audit.router,
):
    app.include_router(router, prefix=settings.api_prefix)


@app.get("/health", tags=["operations"])
def health():
    return {"status": "ok"}


web_dir = Path(__file__).parent / "web"
app.mount("/assets", StaticFiles(directory=web_dir / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def web_app():
    return FileResponse(web_dir / "index.html")


@app.get("/demo", include_in_schema=False)
def web_demo():
    """Render the SPA with local sample data, without requiring authentication."""
    return FileResponse(web_dir / "index.html")
