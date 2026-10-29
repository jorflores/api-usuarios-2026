# API de usuarios · TC2007B

API REST con **Node.js + Express 5 + Prisma 7 + PostgreSQL**, protegida con **JWT**. Es la API de la presentación “API REST con Node.js y Express” y la que va a consumir la app Android con Retrofit.

## Endpoints

| Método | Ruta | Token | Rol | Body | Responde |
|---|---|---|---|---|---|
| GET | `/` | — | — | — | 200 `{ mensaje }` |
| POST | `/login` | — | — | `{ correo, password }` | 200 `{ token }` · 401 |
| GET | `/perfil` | ✔ | cualquiera | — | 200 usuario del token |
| GET | `/usuarios` | ✔ | cualquiera | — | 200 lista |
| GET | `/usuarios/:id` | ✔ | cualquiera | — | 200 · 404 |
| POST | `/usuarios` | ✔ | admin | `{ correo, password, rol? }` | 201 · 400 · 409 |
| PUT | `/usuarios/:id` | ✔ | admin | `{ correo, password, rol }` | 200 · 404 |
| DELETE | `/usuarios/:id` | ✔ | admin | — | 204 · 404 |

- El token va en el header: `Authorization: Bearer <token>`. Dura 1 hora.
- Sin token o con token falso/vencido: **401**. Con token de un `usuario` en una ruta de admin: **403**.
- `rol` es `"admin"` o `"usuario"` (por defecto `"usuario"`).
- **El password nunca sale en una respuesta**: el cliente de Prisma lo omite siempre (ver `src/prisma.js`); solo `/login` lo lee para compararlo.

## Estructura

```
api-usuarios/
├── prisma/
│   ├── schema.prisma          # modelo Usuario -> tabla usuarios
│   ├── migrations/            # SQL que crea la tabla (lo aplica migrate)
│   └── seed.js                # crea/actualiza el admin inicial
├── src/
│   ├── index.js               # Express: middleware, rutas y manejo de errores
│   ├── prisma.js              # PrismaClient con el adaptador de pg
│   └── middleware/auth.js     # verificarToken y soloAdmin
├── prisma.config.js           # Prisma 7: dónde está el schema y DATABASE_URL
├── pruebas.http               # peticiones listas para probar
└── .env.example               # copia como .env
```

## Correr en tu computadora

Requisitos: Node.js 20.19 o más nuevo y una base PostgreSQL. La más fácil es la misma de Render (paso 1 de abajo), usando su **External Database URL**.

```bash
npm install                 # instala y genera el cliente de Prisma
cp .env.example .env        # y llena DATABASE_URL y JWT_SECRET
npx prisma migrate deploy   # crea la tabla usuarios
npm run seed                # crea admin@mail.com / 1234
npm run dev                 # http://localhost:3000, se reinicia al guardar
```

Si te conectas a la base de Render desde tu compu, agrega `?sslmode=require` al final de la External URL (si marca error de certificado, usa `?sslmode=no-verify`).

Para cambiar el modelo: edita `schema.prisma` y corre `npm run db:migrate` (crea una migración nueva).

## Desplegar en Render

1. **Base de datos:** New → Postgres → plan Free. Copia la **Internal Database URL**.
   > La base gratuita vence 30 días después de crearla (más 14 días de gracia antes de borrar los datos).
2. **Sube este proyecto a GitHub** (el `.gitignore` ya excluye `node_modules` y `.env`).
3. **API:** New → Web Service → conecta el repositorio.
   - Build Command: `npm install && npx prisma migrate deploy && npm run seed`
   - Start Command: `npm start`
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

- Los passwords se guardan en texto plano. En producción: `bcrypt.hash` al crear y `bcrypt.compare` en el login.
- Cualquier usuario con sesión puede ver la lista de usuarios. En un sistema real, quizá solo el admin.
