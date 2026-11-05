# SubastAgro Frontend

Aplicación web React + TypeScript para la plataforma SubastAgro, integrada con
la API FastAPI existente. Las pantallas usan los contratos HTTP observados en
`backend/app`; no simulan operaciones para las que el servidor no ofrece una
ruta.

## Requisitos

- Node.js 20.19+ o 22.12+ y npm.
- API backend disponible en `http://localhost:8000`.
- Base de datos y roles inicializados según la guía del backend.

## Instalación y ejecución

Desde PowerShell o una terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Abre <http://localhost:5173>. Para verificar el bundle de producción:

```powershell
npm run build
npm run preview
```

La aplicación también puede configurarse con:

```env
VITE_API_URL=http://localhost:8000
```

El cliente normaliza la URL y añade `/api/v1` si no está presente. Si se usa
otro origen de desarrollo, ese origen debe estar permitido en `CORS_ORIGINS`
del backend. El frontend no lee ni comparte el archivo `.env` del proyecto.

## Integración y sesión

- Axios centraliza las solicitudes bajo `/api/v1` y envía credenciales para
  aceptar la cookie HttpOnly de refresh.
- El access token Bearer permanece únicamente en memoria; no se guarda en
  `localStorage`, `sessionStorage` ni cookies accesibles desde JavaScript.
- Al iniciar, la aplicación intenta restaurar la sesión mediante
  `POST /auth/refresh`. Las respuestas 401 en operaciones protegidas intentan
  una renovación única y reintentan la solicitud original.
- `POST /auth/logout` solicita invalidar el refresh token y limpia la sesión
  local. En producción, el backend debe ejecutarse bajo HTTPS para que marque
  la cookie como `Secure`.
- El indicador de conexión consulta `GET /api/v1/health` periódicamente.
- Los errores HTTP y de validación se muestran en las pantallas que ejecutan
  cada operación.

## Pantallas y permisos

| Perfil | Funcionalidad disponible |
|---|---|
| `ADMINISTRADOR` | Resumen, listado y alta de usuarios, cambio de estado y roles, razas, lotes, programación/edición de subastas, cierre y pago de actas, historial global de pujas y adjudicaciones. |
| `GANADERO` | Resumen, catálogo de razas, creación/edición de sus lotes y consulta/programación de subastas asociadas. |
| `COMPRADOR` | Resumen, subastas activas, envío de pujas, historial propio y actas propias. |
| Todos | Actualización del perfil propio. |

Las rutas de interfaz se ocultan y protegen según roles, pero la autorización
real continúa siendo responsabilidad del backend. Los 401/403/404 de la API se
mantienen visibles y no se reemplazan por datos de ejemplo.

## Contratos disponibles y límites conocidos

El frontend consume las rutas reales actuales, incluyendo:

- Auth: `POST /auth/register`, `/login`, `/refresh`, `/logout`.
- Usuarios: `GET/PATCH /users/me`, `GET /users`, `PATCH /users/{user_id}`.
- Ganado: `GET/POST /breeds`, `PATCH /breeds/{breed_id}`,
  `GET/POST /lots`, `GET/PATCH /lots/{lot_id}` y
  `PATCH /lots/{lot_id}/status`.
- Subastas: `GET/POST /auctions`, `GET/PATCH /auctions/{auction_id}`.
- Pujas: `GET/POST /bids`.
- Adjudicaciones: `GET /adjudications`,
  `POST /adjudications/auctions/{auction_id}/close` y
  `PATCH /adjudications/{id}/payment`.

Limitaciones que dependen de nuevas rutas o permisos del backend:

- No hay endpoint para eliminar lotes, buscar subastas activas por una ruta
  específica, ver el historial de pujas por subasta ni consultar ofertas de
  otros compradores. Las tarjetas de subasta muestran el UUID del lote porque
  el rol comprador no puede usar el endpoint de detalle de lotes.
- No existe push/WebSocket de pujas en tiempo real. La interfaz actual envía
  pujas REST; el servidor valida el mínimo vigente y rechaza una oferta
  insuficiente con el error de negocio correspondiente.
- Las consultas de pujas y adjudicaciones corresponden al comprador autenticado
  (o al administrador), según el backend.
- El backend no ofrece un endpoint separado para asignar roles ni un endpoint
  de registro administrativo. El administrador puede editar el arreglo `roles`
  mediante `PATCH /users/{user_id}`; el registro de cuenta usa
  `POST /auth/register` y permite únicamente comprador o ganadero.
- El estado de la subasta se deriva de las fechas y las pujas; no hay una ruta
  independiente para forzar manualmente `ACTIVA`, `FINALIZADA` o `DESIERTA`.

Estas operaciones deben implementarse en el backend antes de aparecer como
funciones disponibles del frontend.

## Estructura principal

```text
src/
  api/          Axios y catálogo de endpoints
  auth/         Contexto de sesión y guards
  components/   Componentes comunes, formularios, tablas y layout
  context/      Estado de salud de la API
  hooks/        Hooks de presentación
  layouts/      Layouts de autenticación y panel
  pages/        Auth, paneles y operaciones por dominio
  routes/       Rutas React Router
  services/     Funciones de acceso al backend
  styles/       Sistema visual responsive
```
