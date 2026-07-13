"""FastAPI app entry.

Run locally:   uvicorn zero_fir:app --host 0.0.0.0 --port 8002 --reload
Run on prod:   gunicorn zero_fir:app -k uvicorn.workers.UvicornWorker -w 4 -b 127.0.0.1:8002
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.routes_auth import router as auth_router
from api.routes_health import router as health_router
from api.routes_masked import router as masked_router
from api.routes_ncrp import router as ncrp_router
from api.routes_public import router as public_router
from config import settings
from utils.friendly_errors import to_friendly

logger = logging.getLogger(__name__)


# ── Security Headers Middleware ──────────────────────────────────


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


# ── App setup ────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("zeroFIR backend starting.")
    yield
    logger.info("zeroFIR backend shutting down.")


docs_url = None if settings.DISABLE_DOCS else "/docs"
openapi_url = None if settings.DISABLE_DOCS else "/openapi.json"

app = FastAPI(
    title="zeroFIR",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=docs_url,
    openapi_url=openapi_url,
)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ── 422 validation-error handler (CyberFraud lesson from day one) ──


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    raw = exc.errors()
    safe_for_log = [{k: v for k, v in err.items() if k != "input"} for err in raw]
    client_ip = request.client.host if request.client else "?"
    logger.warning(
        "422 %s %s from %s → %s",
        request.method,
        request.url.path,
        client_ip,
        safe_for_log,
    )
    friendly = to_friendly(raw)
    return JSONResponse(status_code=422, content={"detail": "; ".join(friendly)})


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(public_router)
app.include_router(ncrp_router)
app.include_router(masked_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("zero_fir:app", host="0.0.0.0", port=8002, reload=True)
