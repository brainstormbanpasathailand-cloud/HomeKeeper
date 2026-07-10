"""HomeKeeper FastAPI application entrypoint."""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.config import settings
from app.core.ratelimit import limiter
from app.services.storage import LOCAL_DIR

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="HomeKeeper – แพลตฟอร์มดูแลบ้าน รถ และทรัพย์สินตลอดอายุการใช้งาน",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Consistent error envelope; never leak internals in production.
    detail = str(exc) if settings.ENV != "production" else "Internal server error"
    return JSONResponse(status_code=500, content={"error": "internal_error", "detail": detail})


@app.get("/health", tags=["meta"])
def healthcheck():
    return {"status": "ok", "service": settings.PROJECT_NAME, "env": settings.ENV}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Serve locally-stored uploads (fallback when Cloudinary is not configured).
LOCAL_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(LOCAL_DIR)), name="media")
