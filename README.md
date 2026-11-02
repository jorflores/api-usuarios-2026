# API de usuarios · TC2007B

API REST con **Python + FastAPI + SQLAlchemy + PostgreSQL**, protegida con **JWT**.

> Esta es la rama **`fastapi`**: la misma API de la rama `main` (Node.js + Express), reescrita en Python. Tiene **las mismas rutas, el mismo JSON y los mismos códigos de respuesta**, así que la app Android funciona igual con cualquiera de las dos.

FastAPI genera documentación interactiva: con la API corriendo abre **http://localhost:3000/docs** para ver y probar todas las rutas desde el navegador.

## Endpoints

| Método | Ruta | Token | Rol | Body | Responde |
|---|---|---|---|---|---|
| GET | `/` | — | — | — | 200 `{ mensaje }` |
| POST | `/login` | — | — | `{ correo, password }` | 200 `{ token }` · 401 |
| GET | `/perfil` | ✔ | cualquiera | — | 200 usuario del token |
| GET | `/usuarios` | ✔ | cualquiera | — | 200 lista |
| GET | `/usuarios/{id}` | ✔ | cualquiera | — | 200 · 404 |
| POST | `/usuarios` | ✔ | admin | `{ correo, password, rol? }` | 201 · 400 · 409 |
| PUT | `/usuarios/{id}` | ✔ | admin | `{ correo?, password?, rol? }` | 200 · 404 |
| DELETE | `/usuarios/{id}` | ✔ | admin | — | 204 · 404 |

- El token va en el header: `Authorization: Bearer <token>`. Dura 1 hora.
- Sin token o con token falso/vencido: **401**. Con token de un `usuario` en una ruta de admin: **403**.
- `rol` es `"admin"` o `"usuario"` (por defecto `"usuario"`).
- **El password nunca sale en una respuesta**: todas las rutas responden con el esquema `UsuarioOut` (`id`, `correo`, `rol`) de `app/schemas.py`; solo `/login` lee el password para compararlo.
- Los errores siempre responden `{ "error": "..." }`. Si el body o el id no tienen el formato correcto: **400** (FastAPI respondería 422; se cambió para igualar a Express).

## Estructura

```
api-usuarios-2026/
├── app/
│   ├── main.py          # FastAPI: logger, manejo de errores y rutas
│   ├── auth.py          # JWT: crear_token, verificar_token y solo_admin
│   ├── models.py        # modelo Usuario -> tabla usuarios (SQLAlchemy)
│   ├── schemas.py       # forma del JSON que entra y sale (Pydantic)
│   ├── database.py      # conexión a PostgreSQL
│   ├── config.py        # lee DATABASE_URL, JWT_SECRET, etc.
│   └── seed.py          # crea la tabla (si falta) y el admin inicial
├── requirements.txt     # dependencias de Python
├── pruebas.http         # peticiones listas para probar
├── Dockerfile           # imagen de la API
├── docker-compose.yml   # API + PostgreSQL (+ túnel HTTPS opcional)
├── .dockerignore        # lo que no entra a la imagen (.env, .venv)
└── .env.example         # copia como .env
```

### Express → FastAPI

| Express (rama `main`) | FastAPI (esta rama) |
|---|---|
| `app.get('/usuarios/:id', (req, res) => ...)` | `@app.get("/usuarios/{id}")` + `def obtener(id: int)` |
| `req.params.id` + `Number(...)` | `id: int` (FastAPI lo convierte y valida) |
| `req.body` + `express.json()` | Un modelo de Pydantic como parámetro (`datos: UsuarioCrear`) |
| `res.status(201).json(nuevo)` | `status_code=201` en el decorador y `return nuevo` |
| Middleware `verificarToken`, `soloAdmin` | Dependencias: `Depends(verificar_token)`, `Depends(solo_admin)` |
| `req.usuario` | El valor que regresa la dependencia (`token: dict`) |
| Prisma + `omit: { password }` | SQLAlchemy + `response_model=UsuarioOut` |
| `jsonwebtoken` | `PyJWT` |
| `npm install` / `package.json` | `pip install -r requirements.txt` |

## Correr en tu computadora (sin Docker)

Requisitos: Python 3.12 o más nuevo y una base PostgreSQL. La más fácil es la misma de Render, usando su **External Database URL**.

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate      macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # y llena DATABASE_URL y JWT_SECRET
python -m app.seed                # crea la tabla y admin@mail.com / 1234
uvicorn app.main:app --reload --port 3000
```

Si te conectas a la base de Render desde tu compu, agrega `?sslmode=require` al final de la External URL (Render exige SSL en conexiones externas). Si tu `.env` todavía tiene `?sslmode=no-verify` de la versión de Node, también funciona: el código lo convierte.

La tabla se crea sola si no existe. Si ya existe (por ejemplo, la que creó la versión de Node en Render), se reutiliza con sus datos.

## Correr con Docker (API + PostgreSQL local)

Con Docker no necesitas instalar Python ni PostgreSQL: todo corre en contenedores.

### 1. Instalar Docker Desktop (una sola vez)

**Windows**
1. Descarga Docker Desktop de https://www.docker.com/products/docker-desktop/ (**Download for Windows – AMD64**).
2. En el instalador deja **Per-user installation** y **WSL 2**. No marques *Allow Windows Containers*.
3. Si al abrir Docker Desktop aparece **"WSL not installed"**: abre **PowerShell como administrador**, corre
   ```
   wsl --install --no-distribution
   ```
   y **reinicia la computadora**.
4. Abre **Docker Desktop** y espera a que diga **Engine running**.
5. Cierra y vuelve a abrir VS Code (o la terminal) para que reconozca el comando `docker`.

> ¿Ya tienes Hyper-V para los emuladores de Android? No hay problema: WSL 2 usa el mismo hipervisor. Revisa en *Activar o desactivar las características de Windows* que estén marcadas **Plataforma de máquina virtual** y **Plataforma del hipervisor de Windows**.

**macOS**
1. Descarga Docker Desktop para **Apple Silicon** o **Intel** (según tu Mac) de la misma página y arrástralo a Aplicaciones.
2. Ábrelo y espera a que diga **Engine running**.

**Comprobar** (en una terminal nueva):
```
docker --version
docker compose version
docker info
```
Si `docker info` dice *failed to connect to the docker API*, Docker Desktop no está abierto.

### 2. Prender la API

En la carpeta del proyecto:
```
docker compose up --build
```
La primera vez descarga las imágenes de Python y PostgreSQL (unos minutos). Está lista cuando ves:
```
api-1  | Admin listo: { id: 1, correo: 'admin@mail.com', rol: 'admin' }
api-1  | INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)
```
Al arrancar, el contenedor `api` espera a que PostgreSQL esté listo, crea la tabla si falta, crea el admin (`admin@mail.com` / `1234`) y levanta FastAPI.

Prueba http://localhost:3000/docs en el navegador o usa `pruebas.http` con `@base = http://localhost:3000`.

### 3. Comandos útiles

| Comando | Qué hace |
|---|---|
| `docker compose up --build` | Construye y prende todo (los logs quedan en la terminal) |
| `docker compose up --build -d` | Igual, pero en segundo plano |
| `docker compose logs -f api` | Ver los logs de la API |
| `docker compose ps` | Ver qué contenedores están corriendo |
| `docker compose down` | Apaga todo; **los datos se conservan** |
| `docker compose down -v` | Apaga todo y **borra** la base de datos |

- Si cambias el código de `app/`, vuelve a correr `docker compose up --build`.
- Las contraseñas y el `JWT_SECRET` están en `docker-compose.yml`; son **solo para desarrollo**. Tu archivo `.env` no se usa dentro de Docker (lo excluye `.dockerignore`).
- PostgreSQL queda expuesto en `localhost:5432` (usuario y contraseña `postgres`, base `api_usuarios`) por si quieres verlo con pgAdmin o DBeaver.
- Si el puerto 3000 o 5432 ya está ocupado (por ejemplo, otro PostgreSQL instalado), cambia el número de la izquierda en `ports` de `docker-compose.yml`, por ejemplo `"5433:5432"`.

### 4. Opcional: URL HTTPS pública (túnel de Cloudflare)

Para probar desde un **teléfono físico** o sin habilitar HTTP en Android:
```
docker compose --profile https up --build -d
docker compose logs tunnel
```
En el log aparece algo como `https://palabras-al-azar.trycloudflare.com`: esa es la URL de tu API.
- No requiere cuenta. **La URL cambia** cada vez que se reinicia el túnel.
- La API queda **pública** mientras el túnel esté encendido: apágalo con `docker compose --profile https down` cuando termines.

### 5. Dato extra: qué cambiar en la app Android

La app solo cambia su **URL base** (`RetrofitClient.kt`). Elige una opción:

**A. Con el túnel HTTPS (sección 4).** No hay que tocar el manifest:
```kotlin
private const val BASE_URL = "https://palabras-al-azar.trycloudflare.com/"
```

**B. Directo al Docker de tu compu (emulador).** En el emulador, `localhost` es el propio emulador; tu computadora es `10.0.2.2`:
```kotlin
private const val BASE_URL = "http://10.0.2.2:3000/"
```
Como es HTTP sin cifrar, Android lo bloquea. Para permitirlo, en `AndroidManifest.xml`, dentro de `<application ...>`, agrega:
```xml
android:usesCleartextTraffic="true"
```

> En un **teléfono físico** conectado a la misma red Wi-Fi, usa la IP de tu computadora (por ejemplo `http://192.168.1.50:3000/`).

**Para regresar a Render:** vuelve a poner `https://<tu-servicio>.onrender.com/`. Ahí no se necesita `usesCleartextTraffic` (puedes dejarlo o quitarlo).

## Desplegar en Render

1. **Base de datos:** New → Postgres → plan Free. Copia la **Internal Database URL**.
   > La base gratuita vence 30 días después de crearla (más 14 días de gracia antes de borrar los datos).
2. **Sube este proyecto a GitHub** (el `.gitignore` ya excluye `.venv` y `.env`).
3. **API:** New → Web Service → conecta el repositorio y elige la rama `fastapi`.
   - Language: **Python 3**
   - Build Command: `pip install -r requirements.txt && python -m app.seed`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment:
     - `DATABASE_URL` = la Internal Database URL del paso 1
     - `JWT_SECRET` = un texto largo y secreto
     - `ADMIN_CORREO` y `ADMIN_PASSWORD` = el admin inicial
4. Abre `https://<tu-servicio>.onrender.com/` y prueba con `pruebas.http` cambiando `@base`.

> El plan gratuito se duerme tras 15 minutos sin tráfico; la primera petición tarda cerca de un minuto. Ábrela en el navegador antes de la demo.

## Desde Android (Retrofit)

- URL base: `https://<tu-servicio>.onrender.com/` (con `/` al final). Local desde el emulador: `http://10.0.2.2:3000/` + `usesCleartextTraffic="true"` solo en desarrollo.
- Login: `@POST("login") suspend fun login(@Body datos: LoginRequest): LoginResponse` con `LoginRequest(correo, password)` y `LoginResponse(token)`.
- Rutas protegidas: `@Header("Authorization") auth: String` y mandar `"Bearer $token"`.
- DELETE regresa 204 sin body: declara `Response<Unit>` y revisa `isSuccessful` / `code()`.
- El token se guarda por ahora en el ViewModel (memoria); más adelante en DataStore.

## Atajos de clase (no para producción)

- Los passwords se guardan en texto plano. En producción se guardan con hash (por ejemplo, la librería `bcrypt`: `bcrypt.hashpw` al crear y `bcrypt.checkpw` en el login).
- La tabla se crea con `create_all` al arrancar. Si el modelo cambia (columnas nuevas), en un proyecto real se usan migraciones con **Alembic**.
- Cualquier usuario con sesión puede ver la lista de usuarios. En un sistema real, quizá solo el admin.
