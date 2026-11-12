import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_pagination import add_pagination
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import admin_users, audit_logs, auth, permissions, roles
from app.core.config import settings
from app.core.request_context import (
    current_client_ip,
    current_request_id,
    current_user_agent,
    resolve_client_ip,
    resolve_request_id,
    resolve_user_agent,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando MECA API (%s)", settings.ENVIRONMENT)
    yield
    logger.info("MECA API detenida")


app = FastAPI(
    title="MECA API",
    description="API de control presupuestario de Enseña por Bolivia",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "message": "MECA API is running",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

SENSITIVE_PREFIXES = (
    f"{settings.API_V1_PREFIX}/auth",
    f"{settings.API_V1_PREFIX}/users",
    f"{settings.API_V1_PREFIX}/roles",
    f"{settings.API_V1_PREFIX}/permissions",
    f"{settings.API_V1_PREFIX}/audit",
)


@app.middleware("http")
async def security_headers_and_context(request: Request, call_next):
    ip_token = current_client_ip.set(resolve_client_ip(request))
    user_agent_token = current_user_agent.set(resolve_user_agent(request))
    request_id_token = current_request_id.set(resolve_request_id(request))

    try:
        response = await call_next(request)
        if request.method != "OPTIONS":
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains"
            )
            if any(
                request.url.path.startswith(prefix)
                for prefix in SENSITIVE_PREFIXES
            ):
                response.headers["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate"
                )
        return response
    finally:
        current_client_ip.reset(ip_token)
        current_user_agent.reset(user_agent_token)
        current_request_id.reset(request_id_token)


app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["auth"],
)
app.include_router(
    admin_users.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["users"],
)
app.include_router(
    roles.router,
    prefix=f"{settings.API_V1_PREFIX}/roles",
    tags=["roles"],
)
app.include_router(
    permissions.router,
    prefix=f"{settings.API_V1_PREFIX}/permissions",
    tags=["permissions"],
)
app.include_router(
    audit_logs.router,
    prefix=f"{settings.API_V1_PREFIX}/audit",
    tags=["audit"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "Error de validación en %s %s: %s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Datos inválidos",
            "errors": jsonable_encoder(exc.errors()),
        },
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    default_details = {
        404: "Recurso no encontrado",
        405: "Método no permitido",
    }
    detail = default_details.get(exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
        headers=exc.headers,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Error no manejado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


add_pagination(app)