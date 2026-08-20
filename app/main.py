from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.api.routes import audit, auth, expenses, policies
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.services.seed import seed_admin_user


def ensure_sqlite_schema():
    inspector = inspect(engine)
    if "expenses" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("expenses")}
    if "expense_time" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE expenses ADD COLUMN expense_time TIME"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    if engine.url.get_backend_name() == "sqlite":
        Base.metadata.create_all(bind=engine)
        ensure_sqlite_schema()
    seed_admin_user()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
for router in (auth.router, expenses.router, policies.router, audit.router):
    app.include_router(router, prefix=settings.api_prefix)


@app.get("/health", tags=["operations"])
def health():
    return {"status": "ok"}


frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(
        frontend_dir / "index.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )
