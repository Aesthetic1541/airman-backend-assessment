"""
Skynet Flight Operations API
AIRMAN Aeronautics Pvt. Ltd.
"""
import uuid
import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_error_handlers
from app.api.routes import auth, users, bases, aircraft, sorties, training_progress, defects, audit_logs

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("skynet")

app = FastAPI(
    title="Skynet Flight Operations API",
    description="Backend API for AIRMAN Aeronautics — managing sorties, training progress, defects, and dispatch.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request ID + structured logging middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} "
        f"→ {response.status_code} ({duration_ms}ms)"
    )
    response.headers["X-Request-ID"] = request_id
    return response


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
register_error_handlers(app)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(bases.router, prefix=API_PREFIX)
app.include_router(aircraft.router, prefix=API_PREFIX)
app.include_router(sorties.router, prefix=API_PREFIX)
app.include_router(training_progress.router, prefix=API_PREFIX)
app.include_router(defects.router, prefix=API_PREFIX)
app.include_router(audit_logs.router, prefix=API_PREFIX)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "Skynet Flight Operations API", "version": "1.0.0"}