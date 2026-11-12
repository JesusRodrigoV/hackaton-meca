# MECA Backend

Backend FastAPI de MECA. En esta etapa solo están montados los módulos de seguridad:

- autenticación, 2FA, refresh tokens y recuperación de contraseña;
- usuarios administrados;
- roles y matriz de permisos;
- auditoría encadenada.

Los módulos económicos (catálogos, importaciones, movimientos, presupuestos y reportes) quedan fuera de este alcance.

## Requisitos

- Python 3.13
- `uv`
- PostgreSQL
- Redis (opcional; si no está disponible se usa el fallback en memoria para el lockout)

## Configuración

1. Crear el archivo de entorno:

```powershell
Copy-Item .env.example .env
```

2. Completar como mínimo:

- `DATABASE_URL`
- `SECRET_KEY`
- `TOTP_ENCRYPTION_KEY`

Para generar una clave Fernet válida:

```powershell
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

3. Instalar dependencias:

```powershell
uv sync
```

4. Aplicar migraciones:

```powershell
uv run alembic upgrade head
```

La migración crea funciones, triggers, vistas y los seeds de roles, permisos y definiciones de reportes. No crea usuarios.

## Crear el administrador inicial

El alta de administradores es explícita; no hay seed automático ni usuario por defecto.

```powershell
$env:PYTHONPATH="src"
uv run python -m app.scripts.create_admin --email admin@meca.local
```

El comando solicita la contraseña de forma interactiva. También se puede pasar con `--password`, pero no se recomienda porque queda en el historial de la terminal.

Si el correo ya existe, el comando falla sin modificar el usuario.

## Ejecutar la API

```powershell
uv run uvicorn app.main:app --app-dir src --reload
```

- API: `http://localhost:8000`
- Documentación: `http://localhost:8000/docs`
- Salud: `http://localhost:8000/healthz`

## Tests

```powershell
uv run pytest -q
```

Los tests actuales cubren hashing de tokens, emisión/validación de JWT, hashing de contraseñas, autenticación básica, lockout y enforcement de permisos.

## Rutas principales

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/api/v1/auth/login` | Login con email y contraseña |
| POST | `/api/v1/auth/2fa/verify-login` | Segundo paso de login con TOTP o código de respaldo |
| POST | `/api/v1/auth/refresh` | Rotación del refresh token (cookie HttpOnly) |
| POST | `/api/v1/auth/logout` | Cierra la sesión actual |
| POST | `/api/v1/auth/logout-all` | Cierra todas las sesiones del usuario |
| GET | `/api/v1/auth/me` | Perfil y permisos efectivos |
| POST | `/api/v1/auth/change-password` | Cambio de contraseña |
| POST | `/api/v1/auth/forgot-password` | Solicitud genérica de recuperación |
| POST | `/api/v1/auth/reset-password` | Consumo del token de recuperación |
| GET/POST | `/api/v1/auth/2fa/*` | Estado, setup, activación y desactivación de 2FA |
| GET/POST/PUT/DELETE | `/api/v1/users` | Administración de usuarios |
| GET/POST/PUT/DELETE | `/api/v1/roles` | Administración de roles y su matriz |
| GET/POST/PUT/DELETE | `/api/v1/permissions` | Administración de permisos |
| GET | `/api/v1/audit` | Consulta de auditoría |

## Decisiones operativas

- El access token viaja en el cuerpo de la respuesta.
- El refresh token solo viaja en cookie `HttpOnly`, `SameSite=Lax` y `Secure` según el entorno.
- El refresh token rota en cada refresh; el anterior se revoca.
- El logout normal revoca solo la sesión actual; `logout-all` revoca todas.
- Los roles del sistema no se eliminan ni se renombran, pero su matriz de permisos sí se edita.
- Los permisos efectivos se calculan solo por roles; no existe permiso directo por usuario.
- Las contraseñas se validan con la política configurada también en cambio y recuperación.
- La auditoría se escribe en una sesión separada después del commit de negocio.

## Pendientes de configuración

- `CORS_ORIGINS` debe definir el origen real del frontend.
- `FRONTEND_RESET_PASSWORD_URL` debe apuntar a la pantalla real de recuperación.
- `TOTP_ISSUER` queda por defecto en `MECA`; cambiarlo si el nombre visible en el authenticator debe ser otro.