# SubastAgro — hardening de seguridad y despliegue

Guía de configuración de seguridad para el backend FastAPI. Conserva los
dominios y capas `routes.py → services.py → models.py`, con Pydantic para los
contratos y dependencias de seguridad de FastAPI. No sustituye una evaluación
de seguridad independiente ni una prueba de carga del entorno final.

## 1. Perfiles de desarrollo y producción

La configuración central está en `app/core/config.py`. Las variables `APP_*`
son las actuales; se conservan algunos nombres anteriores (`ENVIRONMENT`,
`SECRET_KEY`, `ALGORITHM` y `CORS_ORIGINS`) para entornos existentes.

| Ajuste | Desarrollo | Producción |
| --- | --- | --- |
| `APP_ENV` | `development` | `production` |
| `APP_DEBUG` | Opcional; predeterminado `false` | Debe ser `false` |
| `APP_LOG_LEVEL` | `INFO` o `DEBUG` durante desarrollo | `INFO`/`WARNING` hacia stdout del proceso |
| `APP_JWT_SECRET` | Secreto local aleatorio de 32+ caracteres | Secreto aleatorio, único, gestionado fuera del repositorio |
| `APP_CORS_ORIGINS` | Se agregan los orígenes localhost 5173/3000 | Allowlist explícita; vacía o con `*` no inicia |
| `APP_COOKIE_SECURE` | `false` para HTTP local | `true` (predeterminado automático) |
| `APP_COOKIE_SAMESITE` | `lax` | `lax` (recomendado) |
| Swagger y ReDoc | Disponibles | Deshabilitados |
| Esquema DB al arrancar | Crea tablas y roles faltantes | Solo verifica que migraciones y roles estén aplicados |

Ejemplo local: copia `.env.example` a `.env` y sustituye los valores de
credenciales. Genera un secreto, sin guardarlo en el control de versiones:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Ejemplo de configuración de producción (almacena los valores en el gestor de
secretos del despliegue, no en un archivo versionado):

```env
APP_NAME="SubastAgro API"
APP_ENV=production
APP_DEBUG=false
APP_LOG_LEVEL=INFO
APP_JWT_SECRET=<secreto-aleatorio-de-48-bytes>
APP_JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
APP_COOKIE_SECURE=true
APP_COOKIE_SAMESITE=lax
DATABASE_URL=<url-postgresql-gestionada-con-sslmode-verify-full>
APP_CORS_ORIGINS=["https://subastagro.example.com"]
```

La configuración falla al iniciar si falta la URL/contraseña de PostgreSQL, el
secreto es menor de 32 caracteres o parece un placeholder, producción no declara
orígenes CORS, `APP_DEBUG=true` o la cookie segura se desactiva. No configures
`SameSite=None` sin `Secure`.
Los logs operativos salen por el logger estándar a stdout/stderr del proceso;
no registran credenciales ni tokens. En producción recopílalos en el servicio
de logs de la plataforma, con acceso restringido y retención definida.

En desarrollo se agregan los orígenes `http://localhost:5173` y
`http://localhost:3000`; en producción se usan exclusivamente los orígenes
explícitos. Los métodos permitidos son `GET`, `POST`, `PUT`, `PATCH`, `DELETE` y
`OPTIONS` (`PATCH` es necesario para los recursos que ya exponen ese método).
Los encabezados CORS están limitados a `Authorization`, `Content-Type`,
`Accept` y `Origin`; se permiten credenciales solo junto con una allowlist
explícita, nunca con wildcard.

## 2. Controles de seguridad y OWASP

### RBAC y ownership

| Recurso/acción | ADMINISTRADOR | GANADERO | COMPRADOR |
| --- | --- | --- | --- |
| Usuarios y roles | Administración global | Perfil propio | Perfil propio |
| Lotes | Consulta/moderación global | Crear y administrar solo los propios | Sin administración |
| Subastas | Gestión global | Programar/editar las propias antes del inicio | Ver activas |
| Pujas | Consulta global | Sin acceso | Crear y consultar las propias |
| Actas | Consulta y actualización de pago | Sin acceso | Consultar las propias |
| Cierre de subasta | Sí | No | No |

Las rutas usan dependencias RBAC (`get_current_active_*` o `require_roles`) y
los servicios vuelven a verificar ownership en operaciones por recurso. Las
pujas y actas ajenas se ocultan como `404`; un rol autenticado sin permiso recibe
`403`. El endpoint `GET /api/v1/bids/my-bids` lista únicamente las pujas del
comprador actual; `GET /api/v1/bids` también limita la respuesta para comprador
y permite auditoría global a administradores.

### Controles aplicados

- **A01 Broken Access Control:** dependencias de rol y comprobaciones de
  propiedad en servicios; lotes, pujas y actas tienen cobertura automatizada.
- **A02 Cryptographic Failures:** bcrypt con Passlib; contraseñas nuevas de al
  menos 12 caracteres, con letras y números, y máximo de 72 bytes UTF-8. JWT
  HS256 con duración acotada y secreto obligatorio de al menos 32 caracteres.
- **A03 Injection:** consultas SQL construidas con expresiones SQLAlchemy
  parametrizadas. No se concatenan entradas del usuario en SQL.
- **A05 Security Misconfiguration:** perfiles validados, CORS allowlist,
  documentación desactivada en producción, cookies `HttpOnly`, `SameSite` y
  `Secure`, y encabezados HTTP de seguridad.
- **Autenticación:** la verificación de login ejecuta bcrypt también cuando el
  correo no existe, usando un hash ficticio, para reducir filtraciones por
  diferencias de tiempo. El access token viaja en el cuerpo JSON; el refresh
  token solo se entrega en cookie.
- **Refresh:** el `jti` del refresh se persiste, se rota al renovar y se revoca
  en logout o cambio de contraseña. El backend verifica `Origin` en refresh y
  logout para mitigar CSRF.
- **Exposición de datos:** esquemas de salida no serializan `password_hash`;
  errores de validación no devuelven los valores sensibles recibidos.

Flujo de tokens:

```text
Login ── contraseña ──► API ── bcrypt ──► access JWT en JSON
                                  └──────► refresh JWT en cookie HttpOnly

React ── Authorization: Bearer access ──► endpoints protegidos
React ── cookie + Origin permitido ─────► POST /auth/refresh
API   ── revoca refresh anterior ───────► access nuevo + cookie rotada
Logout ── cookie + Origin permitido ────► revoca sesión y elimina cookie
```

El cliente web debe enviar credenciales en las llamadas de refresh/logout y
mantener el access token en memoria, no en `LocalStorage`. No habilites
`allow_origins=["*"]` con credenciales.

Rutas de propiedad de pujas: `GET /api/v1/bids/my-bids` lista las propias del
comprador y `GET /api/v1/bids/{bid_id}` comprueba ownership antes de responder.

## 3. Migraciones y despliegue productivo

### Preparación de base de datos

La primera migración está versionada en `migrations/versions/`. Crea la base
vacía `subastagro_db` en PostgreSQL y aplica cambios desde `backend/`:

```powershell
python -m venv ..\venv
..\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
alembic upgrade head
```

Configura primero las variables de entorno de producción (`.env` solo es
apropiado para instalaciones controladas y debe quedar fuera de Git). Crea el
administrador inicial con `BOOTSTRAP_ADMIN_EMAIL` y
`BOOTSTRAP_ADMIN_PASSWORD` inyectadas temporalmente en el entorno y ejecuta:

```powershell
python -m app.seed_admin
```

Para cada cambio de esquema, genera y revisa una revisión, pruébala sobre una
copia de datos y despliega antes de iniciar la nueva versión:

```powershell
alembic revision --autogenerate -m "descripcion_del_cambio"
alembic upgrade head
alembic current
```

No uses autogeneración sin revisar el archivo de migración. Para bases
existentes creadas con `create_all`, no ejecutes la migración inicial encima:
verifica primero que el esquema coincide y, solo entonces, registra el baseline
con `alembic stamp head`. Conserva backup y plan de rollback antes de migrar.
En producción, el ciclo de vida de FastAPI verifica el esquema y los roles, no
crea ni modifica tablas automáticamente.

### TLS y proceso ASGI

Termina HTTPS en un balanceador o reverse proxy que valide certificados TLS
modernos, renueve certificados y reenvíe tráfico al proceso ASGI por una
interfaz privada. Configura TLS de PostgreSQL con verificación del certificado
del servidor; usa `sslmode=verify-full` y una CA confiable, no `sslmode=disable`.
No publiques el puerto interno de Uvicorn ni permitas tráfico directo a la API
desde Internet.

Comando sencillo de Uvicorn tras la migración:

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Para Windows local, ejecuta desde `backend/`; en Linux producción usa el
servicio/gestor de procesos del sistema. Si el despliegue usa Gunicorn, instala
el worker ASGI compatible y usa, por ejemplo:

```sh
gunicorn app.main:app --workers 4 --worker-class uvicorn_worker.UvicornWorker \
  --bind 127.0.0.1:8000 --access-logfile - --error-logfile -
```

El mantenimiento periódico de subastas corre dentro de cada proceso de la API;
las operaciones de cierre usan bloqueo transaccional en PostgreSQL para
protegerse de ejecuciones concurrentes. Ajusta el número de workers según
pruebas de carga y confirma en PostgreSQL que los cierres concurrentes no
generen duplicados.

## 4. Validación y límites operativos

Desde `backend/`, ejecuta:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app tests
alembic upgrade head
alembic current
```

Los tests de servicios usan SQLite en memoria; ejecuta además pruebas de
integración, concurrencia de pujas, restauración de backup y carga contra una
instancia PostgreSQL 18 equivalente a producción. Esta aplicación no incorpora
todavía rate limiting distribuido de login, MFA, auditoría persistente ni
protección frente a denegación de servicio; configúralos en un gateway/WAF y
servicios operativos antes de exponerla públicamente. No incluyas tokens,
contraseñas ni URL de conexión en logs.
