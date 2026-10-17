from contextlib import asynccontextmanager
from fastapi import FastAPI
from app import models
from app.database import engine, get_db
from app.routers import items


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager that initializes database tables on startup.
    
    If get_db is overridden (e.g. in test suites using an in-memory database),
    the production database engine is left untouched.
    """
    if get_db not in app.dependency_overrides:
        models.Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="CRUD Analysis App",
    description="A minimal CRUD REST API application using FastAPI, SQLite, and SQLAlchemy.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register API routers
app.include_router(items.router)


@app.get("/health", status_code=200, tags=["health"], summary="Health check endpoint")
def health_check() -> dict:
    """Return a simple health status."""
    return {"status": "ok"}
