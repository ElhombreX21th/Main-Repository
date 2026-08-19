from fastapi import FastAPI

from app.api.routes import audit, auth, expenses, policies
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
for router in (auth.router, expenses.router, policies.router, audit.router):
    app.include_router(router, prefix=settings.api_prefix)


@app.get("/health", tags=["operations"])
def health():
    return {"status": "ok"}
