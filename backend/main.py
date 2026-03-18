import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from db.database import engine, Base
from api.routes import auth, integrations, dashboard, insights, operator

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: DB tabloları oluştur + config doğrula
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Google OAuth credentials kontrolü
    if settings.GOOGLE_CLIENT_ID:
        logger.info(
            "✓ Google OAuth hazır | client_id=%s...%s | redirect_uri=%s",
            settings.GOOGLE_CLIENT_ID[:12],
            settings.GOOGLE_CLIENT_ID[-8:],
            settings.GOOGLE_REDIRECT_URI,
        )
    else:
        logger.warning("✗ GOOGLE_CLIENT_ID boş — OAuth çalışmayacak")

    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Aria API",
    description="AI Marketing OS — Reklam bütçeni boşa harcama.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(insights.router, prefix="/api/v1/insights", tags=["insights"])
app.include_router(operator.router, prefix="/api/v1/operator", tags=["operator"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "aria-backend"}
