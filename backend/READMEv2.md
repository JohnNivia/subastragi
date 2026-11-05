# SubastAgro Backend

API REST modular para gestión de usuarios, ganado, subastas, pujas y adjudicaciones. Stack: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 y PostgreSQL 18.

## Estructura

```text
app/
  auth/          models.py, schemas.py, services.py, routes.py
  users/         models.py, schemas.py, services.py, routes.py
  cattle_lots/   models.py, schemas.py, services.py, routes.py
  auctions/      models.py, schemas.py, services.py, routes.py
  bids/          models.py, schemas.py, services.py, routes.py
  adjudications/ models.py, schemas.py, services.py, routes.py
  core/          config.py, database.py, dependencies.py,
                 exceptions.py, middleware.py, security.py
  main.py
```

Los controladores validan el contrato HTTP, declaran las dependencias de autenticación y delegan operaciones a los servicios. Las consultas, reglas de rol/ownership y transacciones están en `services.py`. La persistencia usa SQLAlchemy 2.0; para una inversión de dependencias estricta, la siguiente evolución arquitectónica sería añadir puertos y adaptadores de repositorio entre servicios y ORM.

## Entidades y cardinalidades

Las ocho entidades funcionales son `usuarios`, `roles`, `usuario_roles`, `razas_ganado`, `lotes_ganado`, `eventos_subasta`, `pujas_ofertas` y `actas_adjudicacion`. UUIDv4 identifican entidades de negocio, excepto `roles`, que conserva PK entera según el modelo relacional. `sesiones_refresh` es una tabla técnica adicional para revocación y rotación de tokens.

- `usuarios` N:M `roles` mediante PK compuesta de `usuario_roles`.
- `usuarios` 1:N `lotes_ganado`; `razas_ganado` 1:N `lotes_ganado`.
- `lotes_ganado` 1:1 `eventos_subasta`, mediante `lote_id UNIQUE`.
- `eventos_subasta` 1:N `pujas_ofertas`.
- `usuarios` 1:N `pujas_ofertas` como comprador.
- `eventos_subasta` 1:1 `actas_adjudicacion`, mediante `subasta_id UNIQUE`.

Las relaciones ORM están declaradas explícitamente. Hay restricciones de unicidad, FK, índices, pesos/cantidades positivos, precios positivos y orden de fechas.

## Configuración y ejecución

Desde la raíz del proyecto, crea/activa el entorno e instala `requirements.txt`. Copia `.env.example` solo si aún no existe `.env`, y configura credenciales PostgreSQL. Se acepta `DATABASE_URL` o las variables `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`. `SECRET_KEY` (o el alias heredado `JWT_SECRET`) debe tener como mínimo 32 caracteres aleatorios; no uses claves de ejemplo en despliegue. `CORS_ORIGINS` admite JSON o lista separada por comas.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Set-Location backend
python -m app.init_db
uvicorn app.main:app --reload
```

El primer administrador se crea con `python -m app.seed_admin`, usando `BOOTSTRAP_ADMIN_EMAIL` y `BOOTSTRAP_ADMIN_PASSWORD` definidos temporalmente fuera de archivos versionados. Swagger UI está en `/docs` durante desarrollo; el health check solicitado está en `/api/v1/health`, con readiness de DB en `/health/ready`.

`app.init_db` sirve para aprovisionamiento inicial, no para evolucionar esquemas existentes. Antes de despliegues con cambios de BD, crea y revisa migraciones versionadas.

## API y seguridad

Prefijo REST: `/api/v1`. Login entrega el access JWT en JSON y establece el refresh JWT en cookie HttpOnly; el refresh rota y el logout/password-change revoca sesiones. El access token se envía en `Authorization: Bearer`. No hay cliente frontend en este repositorio, así que el almacenamiento del access token en el navegador aún debe validarse al implementar React; usar memoria, no LocalStorage.

Los roles son `ADMINISTRADOR`, `GANADERO` y `COMPRADOR`. Las operaciones protegidas requieren usuario activo, rol y ownership. Los compradores solo consultan sus pujas y adjudicaciones; las pujas se serializan con bloqueo de fila y deben superar precio base o mejor puja más incremento mínimo. Los errores 422 excluyen valores recibidos; `core/exceptions.py` centraliza validación, integridad y errores inesperados. SQLAlchemy usa expresiones parametrizadas; los errores de integridad responden 409.

| Dominio | Operaciones principales |
| --- | --- |
| Auth | Registro, login, refresh, logout, cambio de contraseña |
| Users | Perfil propio; listado/actualización administrativa y roles |
| Cattle lots | Catálogo de razas; gestión/ownership de lotes; estado administrativo |
| Auctions | Catálogo por rol, programación y edición antes del inicio |
| Bids | Alta, listado y consulta de pujas; historial inmutable |
| Adjudications | Cierre administrativo, consulta con ownership y estado de pago |

Para producción añade limitación de intentos de login, TLS, auditoría, backups, gestión/rotación de secretos y migraciones. El backend agrega CORS allowlist, cookies `Secure` en producción, encabezados de seguridad y oculta Swagger en producción.

## Cuestionario técnico

1. Conexión PostgreSQL: `app/core/database.py`, usando `settings.sqlalchemy_database_url`.
2. Base ORM: `Base`, derivada de `DeclarativeBase`, en `app/core/database.py`.
3. Errores: handlers en `app/core/exceptions.py`, registrados desde `app/main.py`.
4. Recurso inexistente: los servicios lanzan `HTTPException(404, ...)`.
5. Hash bcrypt: `app/core/security.py`, Passlib `CryptContext`.
6. Asociación N:M: tabla `usuario_roles` en `app/users/models.py`.
7. Usuario con hash: `User` (alias `Usuario`) en `app/users/models.py`.
8. Alta con password plano: `UserCreate` en `app/users/schemas.py`; solo entrada.
9. Respuesta sin hash: `UserResponse` (alias de `UserRead`) en `app/users/schemas.py`.
10. Unicidad de email/documento: `create_user` en `app/users/services.py` y restricciones DB.
11. Login: `POST /api/v1/auth/login` en `app/auth/routes.py`.
12. Sesión DB: `db: Session = Depends(get_db)` en rutas; se pasa al servicio.
13. Routers: `app/main.py`, mediante `app.include_router()`.
14. Health check: `GET /api/v1/health` en `app/main.py`.
15. Grupo de reses: `CattleLot` (alias `LoteGanado`) en `app/cattle_lots/models.py`.
16. Código de lote: `UNIQUE` en modelo y consulta de duplicados en `cattle_lots/services.py`.
17. Evento comercial: `Auction` (alias `EventoSubasta`) en `app/auctions/models.py`.
18. Fechas de subasta: `AuctionCreate` usa `@model_validator` en `app/auctions/schemas.py`; ORM incluye `CHECK`.
19. Oferta: `Bid` (alias `PujaOferta`) en `app/bids/models.py`.
20. Monto mínimo: regla en `app/bids/services.py`.
21. Subasta existente/abierta y rol comprador: `place_bid` en `app/bids/services.py`, además de RBAC dependency.
22. Enum de estado: `EstadoSubasta` (alias `AuctionStatus`) en `app/auctions/schemas.py`.
23. Acta: `Adjudication` (alias `ActaAdjudicacion`) en `app/adjudications/models.py`.
24. Total final: `close_auction` en `app/adjudications/services.py`.
25. Pujas: alta y consultas REST en `app/bids/routes.py`, operaciones en `app/bids/services.py`; el historial no permite edición/borrado.
26. Reglas y transacciones: `services.py` de cada dominio.
27. Endpoints y dependencias HTTP: `routes.py` de cada dominio.
28. Persistencia ORM: `models.py` de cada dominio y `Base` de `core/database.py`.
29. Dependencias: `requirements.txt` en la raíz y copia para instalación desde `backend/`.
30. Arquitectura/seguridad: este `READMEv2.md`.

## Pruebas

Desde `backend/` ejecuta `python -m unittest discover -s tests -v`. Las pruebas de servicios usan SQLite en memoria; las pruebas de contrato/despliegue deben complementarse con PostgreSQL 18 y el frontend cuando se integren.