# Manual de pruebas de API REST — SubastAgro

**Presentación académica:** Prof. LUIS GUILLERMO MORELO  
**Proyecto:** Plataforma de comercialización y subasta de ganado vacuno  
**Versión:** Guía de consumo manual de la API

> Este manual describe el backend y las rutas que existen actualmente. Los
> endpoints que no están implementados se identifican explícitamente para que
> una respuesta `404` o `405` no se interprete como una prueba exitosa de una
> función inexistente. No se afirma que el sistema esté validado en un entorno
> que el estudiante no haya ejecutado.

## 1. Introducción

El propósito de esta guía es permitir al estudiante y al Prof. LUIS GUILLERMO
MORELO iniciar SubastAgro, consumir sus endpoints y revisar manualmente el
resultado de las operaciones y sus controles de acceso.

En este contexto, una **API validada manualmente** es aquella cuyas rutas
documentadas fueron invocadas contra una instancia disponible, con datos de
prueba identificables, y para las que se observó y registró el código HTTP y el
contenido de respuesta esperado. La documentación por sí sola no certifica que
PostgreSQL esté disponible ni que una ejecución haya sido realizada.

El alcance cubre los seis dominios existentes: `auth`, `users`, `cattle_lots`
(incluye razas), `auctions`, `bids` y `adjudications`. Las rutas de sistema
`/health/live`, `/health/ready` y `/api/v1/health` se incluyen como verificaciones
complementarias.

## 2. Herramientas recomendadas

### Swagger UI

En desarrollo, abre `http://localhost:8000/docs`. Permite consultar las rutas
registradas, revisar sus esquemas Pydantic/OpenAPI y ejecutar solicitudes con
**Try it out**. Utiliza **Authorize** y pega el access token; según la
configuración OpenAPI, también puedes escribir `Bearer <token>`. En producción
la aplicación deshabilita `/docs`, `/redoc` y `/openapi.json`.

### Postman o Insomnia

Crea un environment con estas variables:

| Variable | Valor inicial |
| --- | --- |
| `baseUrl` | `http://localhost:8000/api/v1` |
| `token` | Vacío; se asigna desde la respuesta del login |
| `ganaderoToken` | Access token del ganadero de prueba |
| `compradorToken` | Access token del comprador de prueba |
| `adminToken` | Access token del administrador de prueba |
| `loteId`, `razaId`, `subastaId`, `pujaId`, `actaId` | Vacío; se completan con respuestas previas |

Organiza la colección en carpetas por dominio. Para las rutas protegidas,
configura el header `Authorization` con `Bearer {{token}}` (o la variable
específica del rol). El refresh token se transporta en cookie, no como una
variable JSON: habilita el cookie jar de Postman/Insomnia y mantén el origen
`http://localhost:5173` al probar `refresh` y `logout`.

### cURL

Usa `curl` en Linux/macOS y `curl.exe` en Windows PowerShell (evita el alias
PowerShell `curl`). Los ejemplos de PowerShell usan comillas simples para
preservar el JSON. No compartas la salida del login: incluye credenciales de
acceso.

Ejemplo equivalente en Linux/macOS:

```sh
curl -i -c cookies.txt -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  --data-raw '{"email":"comprador.a@example.test","password":"Comprador-Prueba-2026"}'
```

## 3. Preparación del entorno

### 3.1 PostgreSQL y configuración

Instala/inicia PostgreSQL 18 y crea una base vacía llamada `subastagro_db`. El
backend obtiene configuración de `.env` en la raíz del proyecto. La
configuración actualmente consumida por `app/core/config.py` usa
`DATABASE_URL`, `SECRET_KEY` (o `JWT_SECRET`), `ENVIRONMENT` y
`CORS_ORIGINS`; `APP_JWT_SECRET` y `APP_ENV` no son aliases de esa versión de
configuración.

Ejemplo **solo para una instalación local**; sustituye y no reutilices las
credenciales en producción:

```env
DATABASE_URL=postgresql://postgres:CAMBIAR_CLAVE_LOCAL@localhost:5432/subastagro_db
SECRET_KEY=CAMBIAR_POR_UN_SECRETO_ALEATORIO_DE_32_CARACTERES_O_MAS
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

Configura estas variables en `.env`; el `.env.example` del workspace puede usar
aliases `APP_*` que la versión actual de `app/core/config.py` no consume.
Transcribe los nombres compatibles de este bloque en lugar de copiarlo sin
revisar.

`SECRET_KEY` debe contener al menos 32 caracteres. No publiques `.env`, claves,
contraseñas ni tokens. Para crear una clave aleatoria:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Desde PowerShell, en la raíz:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Set-Location backend
python -m app.init_db
uvicorn app.main:app --reload
```

URL base: `http://localhost:8000/api/v1`. `/health/ready` requiere una conexión
válida a la base. En producción, verifica el procedimiento de migraciones
documentado en `READMEv3.md`; `create_all` no es un sistema de migraciones.

### 3.2 Crear usuarios de prueba por rol

La inicialización carga los roles base. El endpoint de registro público permite
crear `GANADERO` y `COMPRADOR`, pero no `ADMINISTRADOR`. Crea el administrador
con `python -m app.seed_admin` después de inicializar la base y establece
temporalmente `BOOTSTRAP_ADMIN_EMAIL` y `BOOTSTRAP_ADMIN_PASSWORD` en el entorno.
Luego registra ganadero y comprador por `POST /auth/register`.

Ejemplo PowerShell para crear el administrador (no guardes la clave en un
archivo):

```powershell
$env:BOOTSTRAP_ADMIN_EMAIL = 'admin@example.test'
$securePassword = Read-Host 'Contraseña admin (12+ caracteres)' -AsSecureString
$env:BOOTSTRAP_ADMIN_PASSWORD = [System.Net.NetworkCredential]::new('', $securePassword).Password
python -m app.seed_admin
Remove-Item Env:BOOTSTRAP_ADMIN_EMAIL, Env:BOOTSTRAP_ADMIN_PASSWORD
```

Ejemplo de registro de ganadero (respuesta `201`):

```powershell
curl.exe -i -X POST 'http://localhost:8000/api/v1/auth/register' `
  -H 'Content-Type: application/json' `
  --data-raw '{"email":"ganadero.a@example.test","password":"Ganadero-Prueba-2026","nombre_completo":"Ganadero A","documento_identidad":"CC-GAN-10001","telefono":"3001234567","rol":"GANADERO"}'
```

Para crear un comprador, cambia el correo, documento, nombre y `rol` a
`COMPRADOR`. Usa direcciones únicas para cada identidad; la solicitud exige
contraseñas de al menos 12 caracteres y hasta 72 bytes UTF-8. La respuesta
contiene datos de perfil/roles, nunca `password_hash`.

Los chequeos de servicio:

```powershell
curl.exe -i 'http://localhost:8000/health/live'
curl.exe -i 'http://localhost:8000/health/ready'
curl.exe -i 'http://localhost:8000/api/v1/health'
```

Esperado: `200` con `{"status":"ok"}` para live/api y `{"status":"ready"}` para
ready cuando PostgreSQL responda.

## 4. Autenticación y autorización JWT

### 4.1 Login

`POST /auth/login` recibe `email` y `password` (no `username`). La respuesta JSON
incluye el access token y datos de usuario. El refresh JWT se entrega aparte en
el header `Set-Cookie`, como cookie `HttpOnly`; no aparece en el JSON.

```powershell
curl.exe -i -c cookies.txt -X POST 'http://localhost:8000/api/v1/auth/login' `
  -H 'Content-Type: application/json' `
  --data-raw '{"email":"comprador.a@example.test","password":"Comprador-Prueba-2026"}'
```

Respuesta ilustrativa `200 OK` (UUIDs, fechas y token son valores variables):

```json
{
  "access_token": "<ACCESS_JWT>",
  "token_type": "bearer",
  "expires_in": 1800,
  "usuario": {
    "id": "09fac9e2-6472-4992-a114-675d9e7ad809",
    "email": "comprador.a@example.test",
    "nombre_completo": "Comprador A",
    "documento_identidad": "CC-COM-20001",
    "telefono": null,
    "estado": true,
    "fecha_creacion": "2026-11-05T10:00:00Z",
    "roles": [
      {
        "id": 3,
        "nombre_rol": "COMPRADOR",
        "descripcion": "Consulta de subastas, pujas y adjudicaciones propias"
      }
    ]
  }
}
```

Guarda el access token solo en una variable de sesión local:

```powershell
$Base = 'http://localhost:8000/api/v1'
$BuyerToken = '<ACCESS_JWT_DEVUELTO_POR_LOGIN>'
$Auth = @{ Authorization = "Bearer $BuyerToken" }
```

Todas las solicitudes protegidas deben llevar:

```http
Authorization: Bearer <ACCESS_JWT>
Content-Type: application/json
```

Si falta el access token, es inválido, expiró o pertenece a una sesión no
activa, se espera `401 Unauthorized`. Un usuario autenticado sin el rol
necesario obtiene normalmente `403 Forbidden`. Para recursos privados ajenos,
los servicios responden `404 Not Found` intencionalmente para ocultar su
existencia.

### 4.2 Refresh y logout

El cookie jar creado con `-c cookies.txt` permite reenviar la cookie HttpOnly
con `-b cookies.txt`. `Origin` debe ser uno de los valores permitidos de CORS:

```powershell
curl.exe -i -b cookies.txt -c cookies.txt -X POST "$Base/auth/refresh" `
  -H 'Origin: http://localhost:5173'
```

`200 OK` devuelve un nuevo `access_token` y rota la cookie refresh. El token
anterior deja de servir para una nueva rotación. Para cerrar la sesión:

```powershell
curl.exe -i -b cookies.txt -c cookies.txt -X POST "$Base/auth/logout" `
  -H 'Origin: http://localhost:5173'
```

La respuesta es `200` con `{"mensaje":"Sesión cerrada"}` y elimina/revoca la
sesión de refresh. Si el cookie falta en refresh, se espera `401`; si el origen
enviado no está permitido, `403`.

## 5. Endpoints reales por dominio

Los ejemplos son solicitudes manuales, no un script de pruebas. Los valores
entre `<...>` se sustituyen por UUIDs o tokens obtenidos en la secuencia. En
consultas sin body no se envía `Content-Type` salvo que el cliente lo requiera.

### 5.1 Auth — `/api/v1/auth`

| Método y ruta | Acceso | Body / resultado |
| --- | --- | --- |
| `POST /auth/register` | Público; solo GANADERO o COMPRADOR | Body como el ejemplo de preparación; `201` con perfil |
| `POST /auth/login` | Público | `email`, `password`; `200`, access JWT JSON y cookie refresh |
| `POST /auth/refresh` | Cookie refresh y origen permitido | Sin body; `200`, tokens rotados |
| `POST /auth/logout` | Cookie refresh; origen permitido si se envía | Sin body; `200`, sesión revocada |
| `POST /auth/password` | Usuario activo con Bearer | `current_password`, `new_password`; `204` sin body |

Cambio de contraseña:

```powershell
curl.exe -i -X POST "$Base/auth/password" `
  -H "Authorization: Bearer $BuyerToken" -H 'Content-Type: application/json' `
  --data-raw '{"current_password":"Comprador-Prueba-2026","new_password":"Nuevo-Comprador-2026"}'
```

No existe `GET /auth/me`; usa `GET /users/me`.

### 5.2 Usuarios — `/api/v1/users`

| Método y ruta | Roles | Body / respuesta |
| --- | --- | --- |
| `GET /users/me` | Cualquier usuario autenticado | `200`, perfil propio |
| `PATCH /users/me` | Cualquier usuario autenticado | Campos de perfil permitidos; `200`, perfil actualizado |
| `GET /users?offset=0&limit=50` | ADMINISTRADOR | `200`, lista paginada |
| `PATCH /users/{user_id}` | ADMINISTRADOR | Perfil, `estado` o roles; `200`, perfil actualizado |

Ejemplo de perfil propio:

```powershell
curl.exe -i "$Base/users/me" -H "Authorization: Bearer $BuyerToken"
curl.exe -i "$Base/users?offset=0&limit=50" -H "Authorization: Bearer $AdminToken"
```

Ejemplo de actualización administrativa:

```powershell
curl.exe -i -X PATCH "$Base/users/<USER_UUID>" `
  -H "Authorization: Bearer $AdminToken" -H 'Content-Type: application/json' `
  --data-raw '{"estado":false}'
```

La API actual no tiene `POST /users`, `GET /users/{id}` ni
`PATCH /users/{id}/status`. El alta pública está en `/auth/register`; la
administración de estado y roles usa `PATCH /users/{user_id}`.

### 5.3 Razas y lotes — `/api/v1/breeds` y `/api/v1/lots`

El dominio se llama `cattle_lots` internamente, pero las rutas registradas son
`/breeds` y `/lots`, no `/cattle-lots`.

| Método y ruta | Roles | Body / respuesta |
| --- | --- | --- |
| `GET /breeds` | Público | `200`, lista de razas activas |
| `POST /breeds` | ADMINISTRADOR | `nombre_raza`, `proposito`; `201` |
| `PATCH /breeds/{breed_id}` | ADMINISTRADOR | Uno o más campos de raza/estado; `200` |
| `GET /lots` | ADMINISTRADOR o GANADERO | `200`; ganadero solo recibe lotes propios |
| `POST /lots` | GANADERO | Body de lote; `201` |
| `GET /lots/{lot_id}` | ADMINISTRADOR o GANADERO propietario | `200` |
| `PATCH /lots/{lot_id}` | ADMINISTRADOR o GANADERO propietario | Campos editables; `200` |
| `PATCH /lots/{lot_id}/status` | ADMINISTRADOR | `estado_lote`: `DISPONIBLE` o `SUSPENDIDO`; `200` |

Crear raza:

```powershell
curl.exe -i -X POST "$Base/breeds" `
  -H "Authorization: Bearer $AdminToken" -H 'Content-Type: application/json' `
  --data-raw '{"nombre_raza":"Brahman","proposito":"Carne"}'
```

La respuesta `201` contiene `id`, `nombre_raza`, `proposito` y `estado`.
Registra el UUID recibido como `$BreedId`. Crear lote:

```powershell
curl.exe -i -X POST "$Base/lots" `
  -H "Authorization: Bearer $SellerToken" -H 'Content-Type: application/json' `
  --data-raw '{"raza_id":"<BREED_UUID>","codigo_lote":"LOT-BRA-0001","cantidad_cabezas":12,"peso_promedio_kg":420.5,"vacunacion_al_dia":true,"ubicacion_hacienda":"Finca El Porvenir, Córdoba"}'
```

La respuesta `201` incluye `id`, `ganadero_id`, `raza_id`, código, cantidad,
peso, vacunación, ubicación y estado. Guarda `id` como `$LotId`.

Consultar los lotes del ganadero autenticado:

```powershell
curl.exe -i "$Base/lots?offset=0&limit=50" `
  -H "Authorization: Bearer $SellerToken"
```

Editar un lote propio:

```powershell
curl.exe -i -X PATCH "$Base/lots/<LOT_UUID>" `
  -H "Authorization: Bearer $SellerToken" -H 'Content-Type: application/json' `
  --data-raw '{"cantidad_cabezas":14,"peso_promedio_kg":425.0}'
```

Respuesta ilustrativa de consulta/creación (`200`/`201`):

```json
{
  "id": "<LOT_UUID>",
  "ganadero_id": "<SELLER_UUID>",
  "raza_id": "<BREED_UUID>",
  "codigo_lote": "LOT-BRA-0001",
  "cantidad_cabezas": 12,
  "peso_promedio_kg": 420.5,
  "vacunacion_al_dia": true,
  "ubicacion_hacienda": "Finca El Porvenir, Córdoba",
  "estado_lote": "DISPONIBLE"
}
```

Consulta catálogo, lista/detalle propio o cambia estado como administrador:

```powershell
curl.exe -i "$Base/breeds"
curl.exe -i "$Base/lots?offset=0&limit=50" -H "Authorization: Bearer $SellerToken"
curl.exe -i "$Base/lots/<LOT_UUID>" -H "Authorization: Bearer $SellerToken"
curl.exe -i -X PATCH "$Base/lots/<LOT_UUID>/status" `
  -H "Authorization: Bearer $AdminToken" -H 'Content-Type: application/json' `
  --data-raw '{"estado_lote":"SUSPENDIDO"}'
```

Las rutas `POST /cattle-lots`, `GET /cattle-lots/my-lots`,
`POST /cattle-lots/breeds` y `GET /cattle-lots/{id}` no existen en esta
implementación. Tampoco hay `DELETE /lots/{id}` en las rutas actuales.

### 5.4 Subastas — `/api/v1/auctions`

| Método y ruta | Roles | Body / respuesta |
| --- | --- | --- |
| `GET /auctions?offset=0&limit=50` | ADMINISTRADOR, GANADERO o COMPRADOR | `200`; comprador ve eventos activos por rango de fechas, ganadero los propios |
| `POST /auctions` | GANADERO propietario del lote o ADMINISTRADOR | Body de programación; `201`, estado inicial `PROGRAMADA` |
| `GET /auctions/{auction_id}` | ADMINISTRADOR, GANADERO propietario o comprador si está activa | `200` |
| `PATCH /auctions/{auction_id}` | GANADERO propietario o ADMINISTRADOR | Cambios permitidos antes del inicio y sin pujas; `200` |

Programa una subasta. Proporciona fechas ISO 8601 con zona horaria; el inicio
debe ser futuro, por eso reemplaza las fechas de ejemplo por valores actuales:

```powershell
curl.exe -i -X POST "$Base/auctions" `
  -H "Authorization: Bearer $SellerToken" -H 'Content-Type: application/json' `
  --data-raw '{"lote_id":"<LOT_UUID>","precio_base_kilo":"8500.00","incremento_minimo_puja":"100.00","fecha_inicio":"<FECHA_UTC_FUTURA>","fecha_cierre":"<FECHA_UTC_POSTERIOR>"}'
```

Ejemplo de formato de fecha: `2026-11-05T17:00:00Z`. Espera hasta que la fecha
de inicio pase para probar pujas. El objeto de respuesta incluye `id`, `lote_id`,
precios, fechas y `estado_subasta`; guarda `id` como `$AuctionId`.

Respuesta ilustrativa de programación (`201`):

```json
{
  "id": "<AUCTION_UUID>",
  "lote_id": "<LOT_UUID>",
  "precio_base_kilo": "8500.00",
  "incremento_minimo_puja": "100.00",
  "fecha_inicio": "2026-11-05T17:00:00Z",
  "fecha_cierre": "2026-11-05T18:00:00Z",
  "estado_subasta": "PROGRAMADA"
}
```

Lista visible para el rol (el comprador recibe únicamente subastas dentro del
rango activo) y consulta un evento por UUID:

```powershell
curl.exe -i "$Base/auctions?offset=0&limit=50" `
  -H "Authorization: Bearer $BuyerToken"
curl.exe -i "$Base/auctions/<AUCTION_UUID>" `
  -H "Authorization: Bearer $BuyerToken"
```

Para editar una subasta programada que aún no comenzó y no tiene pujas:

```powershell
curl.exe -i -X PATCH "$Base/auctions/<AUCTION_UUID>" `
  -H "Authorization: Bearer $SellerToken" -H 'Content-Type: application/json' `
  --data-raw '{"incremento_minimo_puja":"150.00"}'
```

La API no tiene `GET /auctions/active` ni `PATCH /auctions/{id}/status`.
Consulta el recurso con `GET /auctions`; el estado es del ciclo de negocio y no
se cambia mediante una ruta manual de status. Actualizar una subasta iniciada o
con pujas se rechaza con `400`.

### 5.5 Pujas — `/api/v1/bids`

| Método y ruta | Roles | Body / respuesta |
| --- | --- | --- |
| `POST /bids` | COMPRADOR | `subasta_id`, `monto_ofertado_kilo`; `201` |
| `GET /bids?offset=0&limit=50` | COMPRADOR o ADMINISTRADOR | Comprador: solo propias; administrador: global; `200` |
| `GET /bids/{bid_id}` | COMPRADOR propietario o ADMINISTRADOR | `200`; puja ajena/no existente: `404` |

La primera oferta debe ser al menos el precio base; las siguientes deben
alcanzar la puja máxima más el incremento mínimo:

```powershell
curl.exe -i -X POST "$Base/bids" `
  -H "Authorization: Bearer $BuyerToken" -H 'Content-Type: application/json' `
  --data-raw '{"subasta_id":"<AUCTION_UUID>","monto_ofertado_kilo":"8500.00"}'
```

La respuesta `201` incluye `id`, `subasta_id`, `comprador_id`,
`monto_ofertado_kilo` y `fecha_hora_puja`. Guarda el `id` como `$BidId`.
Realiza otra puja aumentando al menos el incremento configurado para comprobar
la regla.

Respuesta ilustrativa (`201`):

```json
{
  "id": "<BID_UUID>",
  "subasta_id": "<AUCTION_UUID>",
  "comprador_id": "<BUYER_UUID>",
  "monto_ofertado_kilo": "8500.00",
  "fecha_hora_puja": "2026-11-05T17:05:00Z"
}
```

El historial del comprador con `GET /bids` contiene solo sus pujas. Para un
detalle individual:

```powershell
curl.exe -i "$Base/bids?offset=0&limit=50" `
  -H "Authorization: Bearer $BuyerToken"
curl.exe -i "$Base/bids/<BID_UUID>" `
  -H "Authorization: Bearer $BuyerToken"
```

`GET /bids` es la consulta del historial propio para COMPRADOR; no existe
`GET /bids/my-bids` ni `GET /bids/auction/{auction_id}` en las rutas actuales.
Tampoco existe una operación PATCH de pujas; el historial no puede alterarse
por endpoint.

### 5.6 Adjudicaciones — `/api/v1/adjudications`

| Método y ruta | Roles | Body / respuesta |
| --- | --- | --- |
| `POST /adjudications/auctions/{auction_id}/close` | ADMINISTRADOR | Sin body; `200` con acta ganadora o `null` si desierta |
| `GET /adjudications?offset=0&limit=50` | COMPRADOR o ADMINISTRADOR | Comprador: propias; administrador: global; `200` |
| `GET /adjudications/{adjudication_id}` | Comprador ganador o ADMINISTRADOR | `200`; ajena/no existente: `404` |
| `PATCH /adjudications/{adjudication_id}/payment` | ADMINISTRADOR | `{"estado_pago":"PAGADO"}`; `200` |

El cierre debe ejecutarse después de la fecha fin de la subasta:

```powershell
curl.exe -i -X POST "$Base/adjudications/auctions/<AUCTION_UUID>/close" `
  -H "Authorization: Bearer $AdminToken"
```

Con pujas, la respuesta incluye `id`, subasta, comprador ganador, puja
ganadora, total final, código único `guia_movilizacion_codigo`, estado de pago
`PENDIENTE` y fecha de cierre. El total se calcula como peso promedio × cabezas
× precio ganador por kilo. Sin pujas, el cierre devuelve `null` y el lote vuelve
a estar disponible. Guarda el `id` del acta como `$AdjudicationId`.

Ejemplo de respuesta con ganador (`200`):

```json
{
  "id": "<ADJUDICATION_UUID>",
  "subasta_id": "<AUCTION_UUID>",
  "comprador_ganador_id": "<BUYER_UUID>",
  "puja_ganadora_id": "<BID_UUID>",
  "monto_total_final": "42840000.00",
  "guia_movilizacion_codigo": "SAG-<CODIGO_UNICO>",
  "estado_pago": "PENDIENTE",
  "fecha_cierre": "2026-11-05T18:00:00Z"
}
```

Consulta historial propio, detalle y cambia el estado de pago como admin:

```powershell
curl.exe -i "$Base/adjudications?offset=0&limit=50" `
  -H "Authorization: Bearer $BuyerToken"
curl.exe -i "$Base/adjudications/<ADJUDICATION_UUID>" `
  -H "Authorization: Bearer $BuyerToken"
curl.exe -i -X PATCH "$Base/adjudications/<ADJUDICATION_UUID>/payment" `
  -H "Authorization: Bearer $AdminToken" -H 'Content-Type: application/json' `
  --data-raw '{"estado_pago":"PAGADO"}'
```

El comprador consulta las actas propias mediante `GET /adjudications`; no existe
`GET /adjudications/my-adjudications`. La ruta de cierre real es
`/adjudications/auctions/{auction_id}/close`, no
`/adjudications/close-auction/{auction_id}`.

## 6. Pruebas manuales RBAC y Ownership

Usa dos ganaderos (`$SellerToken`, `$SellerBToken`) y dos compradores
(`$BuyerToken`, `$BuyerBToken`) con recursos creados por cada identidad.

| Escenario | Solicitud | Resultado esperado |
| --- | --- | --- |
| COMPRADOR intenta crear lote | `POST /lots` con `$BuyerToken` y body válido | `403 Forbidden` por rol |
| GANADERO intenta modificar puja | `PATCH /bids/<BID_UUID>` con `$SellerToken` | `405 Method Not Allowed`: no existe ruta PATCH de pujas |
| Ganadero A accede al detalle de lote de Ganadero B | `GET /lots/<LOT_B>` con `$SellerToken` | `404 Not Found` para ocultar ownership |
| Ganadero A edita lote de Ganadero B | `PATCH /lots/<LOT_B>` con `$SellerToken` | `404 Not Found` |
| Comprador A consulta puja de Comprador B | `GET /bids/<BID_B>` con `$BuyerToken` | `404 Not Found` |
| Comprador A consulta acta de Comprador B | `GET /adjudications/<ACTA_B>` con `$BuyerToken` | `404 Not Found` |
| Ganadero consulta pujas | `GET /bids` con `$SellerToken` | `403 Forbidden` |
| Token ausente | Ruta que requiere autenticación sin `Authorization` | `401 Unauthorized` |
| ADMINISTRADOR crea lote como vendedor | `POST /lots` | `403 Forbidden`; esa ruta requiere rol GANADERO |

> En detalle de recursos ajenos, la implementación usa **404**, no 403. Esta
> respuesta deliberadamente oculta si el UUID existe. El ejemplo de GANADERO
> modificando una puja debe producir **405**, no 403, porque no hay una ruta
> `PATCH /bids/{id}`. No se debe presentar esos resultados como 403.

Ejemplo ejecutable para comprobar el rechazo de rol:

```powershell
curl.exe -i -X POST "$Base/lots" `
  -H "Authorization: Bearer $BuyerToken" -H 'Content-Type: application/json' `
  --data-raw '{"raza_id":"<BREED_UUID>","codigo_lote":"LOT-NO-AUTORIZADO","cantidad_cabezas":2,"peso_promedio_kg":400,"vacunacion_al_dia":true,"ubicacion_hacienda":"Finca de prueba"}'
```

Ejemplo para comprobar ocultamiento de lote ajeno:

```powershell
curl.exe -i "$Base/lots/<LOT_DE_GANADERO_B>" `
  -H "Authorization: Bearer $SellerToken"
```

## 7. Errores HTTP y validación de datos

Los handlers traducen errores de validación a `422`, integridad de base de datos
a `409` y excepciones inesperadas a `500` genérico. Las reglas de negocio usan
`400`; autorización usa `401`/`403`; recursos no disponibles o ajenos usan `404`.

| Código | Causa común | Ejemplo de respuesta |
| --- | --- | --- |
| `200` | Consulta o actualización correcta | JSON del recurso/lista |
| `201` | Registro, lote, raza, subasta o puja creada | JSON del recurso creado |
| `204` | Cambio de contraseña correcto | Sin contenido |
| `400` | Oferta menor al mínimo, subasta cerrada o regla de negocio | `{"detail":"La oferta mínima permitida es 8600.00"}` |
| `401` | Token ausente/expirado, credenciales incorrectas o refresh inválido | `{"detail":"Credenciales inválidas o expiradas"}` |
| `403` | Rol no autorizado u origen no permitido | `{"detail":"No tienes permisos para realizar esta operación"}` |
| `404` | UUID inexistente, recurso ajeno o subasta no visible | `{"detail":"Lote no encontrado"}` |
| `405` | Método HTTP no implementado para una ruta | `{"detail":"Method Not Allowed"}` |
| `409` | Conflicto de integridad/único | `{"detail":"El recurso entra en conflicto con datos existentes"}` |
| `422` | JSON mal formado o campo/tipo fuera del esquema | ver ejemplo abajo |
| `503` | Base no disponible en readiness | `{"detail":"Base de datos no disponible"}` |

Ejemplo de puja inferior al mínimo (`400`):

```json
{"detail":"La oferta mínima permitida es 8600.00"}
```

Ejemplo de validación de tipo/campo (`422`; el detalle exacto puede depender de
Pydantic):

```json
{
  "detail": [
    {
      "loc": ["body", "cantidad_cabezas"],
      "msg": "Input should be a valid integer",
      "type": "int_parsing"
    }
  ]
}
```

Prueba enviando `cantidad_cabezas` como `"muchas"` o un UUID mal formado. La
respuesta de validación no debe incluir valores sensibles como contraseñas.

## 8. Swagger UI / OpenAPI

1. Inicia FastAPI en desarrollo y abre `http://localhost:8000/docs`.
2. Expande una operación para ver parámetros, body JSON, esquema de respuesta
   y posibles códigos HTTP.
3. Pulsa **Try it out**, reemplaza los UUID de ejemplo por los recibidos en
   solicitudes anteriores y ejecuta **Execute**.
4. Después de `POST /auth/login`, copia `access_token` de la respuesta.
5. Pulsa **Authorize**. Si aparece el esquema Bearer, pega el token según la
   interfaz indique (con o sin el prefijo `Bearer`); luego prueba rutas
   protegidas.
6. La cookie refresh es `HttpOnly`; Swagger/JavaScript no debe intentar leer su
   valor. Para refresh/logout, utiliza un cliente con cookie jar habilitado y un
   origen permitido.
7. Revisa los esquemas bajo **Schemas** al final de `/docs`. Los modelos
   describen validación Pydantic v2, campos obligatorios y respuestas.

## 9. Checklist de entrega

Marca un punto solo después de ejecutar la solicitud en el entorno indicado y
anotar fecha, resultado HTTP y evidencia (sin secretos ni tokens):

- [ ] Base `subastagro_db` creada y conectividad `/health/ready` confirmada en PostgreSQL 18.
- [ ] Roles iniciales y usuario administrador preparados.
- [ ] Registro de GANADERO/COMPRADOR y login probados; `password_hash` no aparece en JSON.
- [ ] Refresh rota el cookie; logout invalida la sesión.
- [ ] Raza y lote creados; ganadero consulta únicamente sus lotes.
- [ ] Subasta programada con fechas ISO 8601 válidas y precio base/incremento comprobados.
- [ ] Puja mínima aceptada y puja por debajo del mínimo rechazada con `400`.
- [ ] Cierre posterior a la fecha fin genera acta/guía o marca desierta si no hay pujas.
- [ ] Compradores consultan sus propios historiales/actas; accesos a UUID ajenos devuelven `404`.
- [ ] Intentos RBAC no autorizados devuelven `401` o `403`, según corresponda.
- [ ] Los métodos y rutas no implementados se registran como pendientes (no como validación exitosa).

**Estudiante/equipo:** ____________________________________  
**Fecha de ejecución:** ___________________________________  
**Firma:** _______________________________________________

## 10. Conclusión

Este manual permite ejecutar una revisión manual reproducible, pero no declara
por sí mismo el sistema “100 % validado” ni “listo para producción”. Esa
conclusión requiere completar el checklist con evidencia real, validar
integración y concurrencia contra PostgreSQL 18 y verificar el despliegue bajo
TLS. Las rutas que el enunciado solicita y no están implementadas quedan
identificadas para desarrollo futuro: `/auth/me`, CRUD directo `/users`,
`/cattle-lots/*`, `/auctions/active`, actualización manual de estado de subasta,
historial por subasta y alias `my-bids`/`my-adjudications`.
