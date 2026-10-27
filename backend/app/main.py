"""FastAPI application entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.rate_limit import RateLimiter, RateLimitMiddleware
from app.routers import auth, conversations, usage

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend API for the AI Chat Platform: auth, persisted conversations, "
        "streaming AI chat with lightweight RAG grounding, rate limiting and "
        "usage metering."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

limiter = RateLimiter(capacity_per_minute=settings.rate_limit_messages_per_minute)

# Order matters: Starlette's *last*-added middleware wraps the *outermost*
# layer. RateLimitMiddleware is added first so CORSMiddleware (added last)
# still applies its headers to 429 responses the rate limiter short-circuits.
app.add_middleware(RateLimitMiddleware, limiter=limiter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(usage.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
