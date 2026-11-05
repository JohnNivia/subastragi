# SubastAgro API

Guía de la primera versión. La arquitectura y contratos vigentes están documentados en [READMEv2.md](READMEv2.md).

Backend REST para gestión de ganado, subastas, pujas y adjudicaciones. Está organizado por dominios en `app/` y usa FastAPI, Pydantic v2, SQLAlchemy 2.0 y PostgreSQL.

## Arquitectura

- `auth`: registro, login, JWT de acceso y refresh tokens rotatorios en cookie HttpOnly. Las sesiones refresh se almacenan revocables.
- `users`: perfiles, catálogo de roles y administración RBAC.
- `cattle_lots`: razas, lotes y control de ownership del ganadero.
- `auctions`: programación, catálogo y estado de subastas.
- `bids`: historial y validación serializada de pujas.
- `adjudications`: cierre, ganador, total financiero y guía de movilización.
- `core`: configuración, base SQLAlchemy, seguridad, dependencias y encabezados HTTP.

Las ocho entidades funcionales son `usuarios`, `roles`, `usuario_roles`, `razas_ganado`, `lotes_ganado`, `eventos_subasta`, `pujas_ofertas` y `actas_adjudicacion`. `sesiones_refresh` es una tabla técnica adicional para revocar y rotar refresh tokens sin almacenar los JWT en claro.

## Requisitos

- Python 3.11 o posterior.
- PostgreSQL 18, con una base creada llamada `subastagro_db`.
- PowerShell en Windows (los comandos de activación para otros shells se indican abajo).

## Instalación

Desde la raíz del repositorio:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

En Linux/macOS, activa el entorno con `source venv/bin/activate`.

Edita `.env` con las credenciales de PostgreSQL. `DATABASE_URL` puede usarse en lugar de `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD`. `SECRET_KEY` (o el nombre heredado `JWT_SECRET`) debe ser aleatorio y tener al menos 32 caracteres. Para generar uno:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

No uses las credenciales de ejemplo en despliegues. `.env` está excluido de Git. `CORS_ORIGINS` acepta un arreglo JSON o una lista separada por comas. `ACCESS_TOKEN_MINUTES` también se admite por compatibilidad con la configuración previa.

## Inicialización y ejecución

La primera vez, inicializa las tablas y el catálogo de roles:

```powershell
Set-Location backend
python -m app.init_db
```

Crea el administrador inicial con variables temporales de entorno. No guardes su contraseña en archivos versionados:

```powershell
$env:BOOTSTRAP_ADMIN_EMAIL = "admin@tu-dominio.example"
$securePassword = Read-Host "Contraseña inicial (12+ caracteres)" -AsSecureString
$env:BOOTSTRAP_ADMIN_PASSWORD = [System.Net.NetworkCredential]::new("", $securePassword).Password
python -m app.seed_admin
Remove-Item Env:BOOTSTRAP_ADMIN_EMAIL, Env:BOOTSTRAP_ADMIN_PASSWORD
```

Inicia el servidor desde `backend/`:

```powershell
uvicorn app.main:app --reload
```

La API queda en `http://127.0.0.1:8000`, Swagger UI en `/docs`, y los chequeos de salud en `/health/live` y `/health/ready`. En producción, documenta y ejecuta migraciones revisadas antes de desplegar; `app.init_db` está destinado al aprovisionamiento inicial y no sustituye un flujo de migraciones para cambios de esquema.

## Esquema PostgreSQL

| Tabla | Responsabilidad / restricciones principales |
| --- | --- |
| `usuarios` | UUID, email y documento únicos, contraseña bcrypt, contacto y estado |
| `roles` | Catálogo único: `ADMINISTRADOR`, `GANADERO`, `COMPRADOR` |
| `usuario_roles` | Asociación N:M con PK compuesta |
| `razas_ganado` | Catálogo de raza, propósito y estado |
| `lotes_ganado` | Propietario, raza, código único, cantidad y peso positivos |
| `eventos_subasta` | Una subasta por lote; precios positivos y cierre posterior al inicio |
| `pujas_ofertas` | Historial por comprador; montos `NUMERIC(12,2)` |
| `actas_adjudicacion` | Una adjudicación por subasta, puja ganadora y guía única |
| `sesiones_refresh` | Sesiones auxiliares revocables, vinculadas a usuarios |

Los UUID se almacenan como `UUID`, fechas como `TIMESTAMP WITH TIME ZONE` y valores monetarios como `NUMERIC`, evitando errores de punto flotante en ofertas y adjudicaciones.

## Contrato API

Prefijo: `/api/v1`. Los cuerpos y respuestas usan JSON; los campos desconocidos se rechazan. La autenticación de API usa `Authorization: Bearer <access_token>`. Login devuelve el token de acceso y establece el refresh token en cookie HttpOnly; `/auth/refresh` rota la cookie y `/auth/logout` revoca la sesión.

| Método | Ruta | Acceso |
| --- | --- | --- |
| POST | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout` | Público / cookie refresh |
| POST | `/auth/password` | Usuario autenticado; revoca sus refresh tokens |
| GET, PATCH | `/users/me` | Usuario autenticado |
| GET, PATCH | `/users`, `/users/{user_id}` | Administrador |
| GET, POST, PATCH | `/breeds`, `/breeds/{breed_id}` | Lectura pública / administrador |
| GET, POST | `/lots` | Ganadero propio; administrador global |
| PATCH | `/lots/{lot_id}` | Ganadero propietario o administrador |
| PATCH | `/lots/{lot_id}/status` | Administrador |
| GET, POST, PATCH | `/auctions`, `/auctions/{auction_id}` | Comprador ve activas; ganadero programa/edita propias aún no iniciadas; administrador global |
| POST, GET | `/bids` | Comprador; administrador audita |
| GET | `/adjudications` | Comprador solo propias; administrador audita |
| PATCH | `/adjudications/{id}/payment` | Administrador |
| POST | `/adjudications/auctions/{auction_id}/close` | Administrador |

La puja mínima es el precio base si aún no existen ofertas; en caso contrario, es la mejor oferta más el incremento mínimo. El servidor serializa pujas por subasta mediante bloqueo de fila. Al cierre, el total es precio ganador por kilo multiplicado por cabezas y peso promedio.

## Seguridad y operación

- Los usuarios públicos solo pueden registrarse como `GANADERO` o `COMPRADOR`; el administrador se aprovisiona por el comando aislado.
- El backend vuelve a comprobar usuario activo, rol y ownership en cada operación protegida. Los recursos ajenos se ocultan con 404 en rutas de detalle.
- Contraseñas con bcrypt; los tokens de acceso son JWT HS256 de vida corta. Los refresh tokens rotan, se revocan al cerrar sesión y no se guardan en claro.
- CORS usa allowlist de orígenes, credenciales habilitadas y encabezados/métodos explícitos. Las cookies son `HttpOnly`, `SameSite=Lax` y `Secure` en producción.
- Se agregan encabezados anti-sniffing, anti-framing, política de referrer y HSTS en producción. No se habilita `/docs` en producción.
- La aplicación no crea tablas automáticamente al arrancar. Errores de validación son 422; credenciales inválidas 401; permisos 403; conflictos de negocio 400 y conflictos de integridad 409.
- Configura límites de tasa de login, TLS, backups, rotación de secretos y logging/auditoría en el proxy/plataforma de despliegue. CORS y JWT por sí solos no reemplazan esos controles.

## Validación

Desde `backend/`, comprueba que la aplicación puede cargar y que la configuración de base de datos está accesible:

```powershell
python -c "from app.main import app; print(app.title)"
python -c "from app.main import readiness; print(readiness())"
python -m unittest discover -s tests -v
```

La segunda comprobación requiere que PostgreSQL esté activo y que el `.env` apunte a `subastagro_db`.