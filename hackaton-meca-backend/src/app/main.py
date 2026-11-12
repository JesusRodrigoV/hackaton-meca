from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from fastapi.concurrency import run_in_threadpool
import logging

from fastapi_pagination import add_pagination
from app.core.config import settings
from app.core.request_context import current_client_ip, resolve_client_ip
from app.scripts.create_admin import create_default_admin
from app.scripts.seeds import init_db
from app.core.scheduler import scheduler, setup_scheduler

from app.api.v1 import (
    auth,
    animals,
    admin_users,
    favorite_animals,
    surveys,
    trivia,
    vendp,
    inventario_admin,
    transacciones,
    alimentacion,
    tareas,
    veterinario,
    dashboards,
    reportes,
    onboarding,
    permissions,
    roles,
    audit_logs,
    information_assets,
    risk_matrix,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando ZooConnect API")

    logger.info("Verificando datos semilla")
    await run_in_threadpool(init_db)

    logger.info("Verificando usuario administrador")
    await run_in_threadpool(create_default_admin)

    logger.info("Iniciando Scheduler")
    setup_scheduler()

    logger.info("Verificacion exitosa")

    yield

    logger.info("Apagando ZooConnect")
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler detenido")
    logger.info("ZooConnect API detenida")


app = FastAPI(
    title="ZooConnect API",
    lifespan=lifespan,
    description="API para la gestion de un zoologico",
    version="5.0.0",
)

@app.get("/")
async def root():
    return {"message": "ZooConnect API is running", "docs": "/docs", "version": "5.0.0"}

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# Log de orígenes permitidos para depuración en Render
logger.info("Configurando CORS con orígenes: %s", settings.CORS_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

SENSITIVE_PREFIXES = (
    "/zooconnect/auth",
    "/zooconnect/admin_users",
    "/zooconnect/audit",
    "/zooconnect/veterinario",
    "/zooconnect/reportes",
    "/zooconnect/security",
    "/zooconnect/inventario",
    "/zooconnect/transacciones",
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    current_client_ip.set(resolve_client_ip(request))

    # Optimización para CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = (
        "max-age=63072000; includeSubDomains"
    )
    if any(request.url.path.startswith(prefix) for prefix in SENSITIVE_PREFIXES):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


app.include_router(auth.router, prefix="/zooconnect/auth", tags=["auth"])
app.include_router(admin_users.router, prefix="/zooconnect/admin_users", tags=["admin"])
app.include_router(
    permissions.router,
    prefix="/zooconnect/admin_users/permissions",
    tags=["permissions"],
)
app.include_router(roles.router, prefix="/zooconnect/admin_roles", tags=["roles"])
app.include_router(audit_logs.router, prefix="/zooconnect/audit", tags=["audit"])
app.include_router(information_assets.router, prefix="/zooconnect/information-assets", tags=["information-assets"])
app.include_router(risk_matrix.router, prefix="/zooconnect/risk-matrix", tags=["risk-matrix"])
app.include_router(animals.router, prefix="/zooconnect/animals")
app.include_router(surveys.router, prefix="/zooconnect/surveys")
app.include_router(trivia.router, prefix="/zooconnect/trivia", tags=["trivia"])
app.include_router(favorite_animals.router, prefix="/zooconnect/favorite_animals")
app.include_router(
    vendp.router, prefix="/zooconnect/security", tags=["Seguridad"]
)
app.include_router(
    inventario_admin.router,
    prefix="/zooconnect/inventario",
    tags=["Inventario"],
)
app.include_router(
    transacciones.router,
    prefix="/zooconnect/transacciones",
    tags=["Entradas y salidas de inventario"],
)
app.include_router(
    alimentacion.router, prefix="/zooconnect/alimentacion", tags=["Alimentacion"]
)
app.include_router(tareas.router, prefix="/zooconnect/tareas", tags=["Tareas"])
app.include_router(
    veterinario.router, prefix="/zooconnect/veterinario", tags=["Veterinario"]
)
app.include_router(dashboards.router, prefix="/zooconnect/dashboards", tags=["Dashboards"])
app.include_router(reportes.router, prefix="/zooconnect/reportes", tags=["Reportes"])
app.include_router(
    onboarding.router, prefix="/zooconnect/onboarding", tags=["Onboarding"]
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Error de validacion en %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": "Datos invalidos", "errors": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Error no manejado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


add_pagination(app)
