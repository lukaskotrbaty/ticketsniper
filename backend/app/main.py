from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api.api import api_router

# SQLAdmin imports
from sqladmin import Admin
from app.admin.auth import authentication_backend
from app.admin.views import admin_views_to_register

# Lifespan context manager to create DB tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Rate Limiter state if needed (MemoryStorage doesn't require specific init)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Clean up resources if needed on shutdown
    await engine.dispose()


app = FastAPI(title="Ticket Sniper", lifespan=lifespan, docs_url=None, redoc_url=None)

# Configure CORS using settings from config.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SQLAdmin
# The `engine` is your SQLAlchemy async engine, already imported
admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=authentication_backend,
    base_url="/admin"  # This will make the admin available at /admin
)

# Register ModelViews with SQLAdmin
for view in admin_views_to_register:
    admin.add_view(view)


@app.get("/")
async def read_root():
    return {"message": "Welcome to Ticket Sniper API"}


app.include_router(api_router, prefix="/api/v1")
