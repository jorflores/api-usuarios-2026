# API de usuarios con FastAPI. Mismas rutas, JSON y códigos que la versión de Express.
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import crear_token, solo_admin, verificar_token
from app.database import Base, engine, get_db
from app.models import Usuario
from app.schemas import (
    LoginRequest,
    TokenResponse,
    UsuarioActualizar,
    UsuarioCrear,
    UsuarioOut,
)

ROLES = ["admin", "usuario"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea la tabla "usuarios" si todavía no existe (si ya existe, no la toca).
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="API de usuarios · TC2007B", lifespan=lifespan)


# ── Middleware: logger ───────────────────────────────────────────────
@app.middleware("http")
async def logger(request: Request, call_next):
    print(f"{request.method} {request.url.path}", flush=True)
    return await call_next(request)


# ── Errores: siempre responden { "error": "..." } ───────────────────
@app.exception_handler(HTTPException)
async def error_http(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def error_validacion(request: Request, exc: RequestValidationError):
    # FastAPI respondería 422; usamos 400 como la versión de Express.
    return JSONResponse(status_code=400, content={"error": "Datos no válidos"})


@app.exception_handler(IntegrityError)
async def error_integridad(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={"error": "Ese correo ya está registrado"})


@app.exception_handler(Exception)
async def error_general(request: Request, exc: Exception):
    print(exc, flush=True)
    return JSONResponse(status_code=500, content={"error": "Error interno"})


def buscar_o_404(db: Session, id: int) -> Usuario:
    usuario = db.get(Usuario, id)
    if not usuario:
        raise HTTPException(status_code=404, detail="No encontrado")
    return usuario


# ── Rutas públicas ──────────────────────────────────────────────────
@app.get("/")
def raiz():
    return {"mensaje": "API de usuarios funcionando"}


# POST /login  { correo, password }  ->  { token }
@app.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest | None = None, db: Session = Depends(get_db)):
    if not datos or not datos.correo or not datos.password:
        raise HTTPException(status_code=400, detail="Faltan correo o password")
    usuario = db.scalar(select(Usuario).where(Usuario.correo == datos.correo))
    if not usuario or usuario.password != datos.password:
        raise HTTPException(status_code=401, detail="No autorizado")
    return {"token": crear_token(usuario.id, usuario.rol)}


# ── De aquí para abajo, todo pide token ─────────────────────────────

# GET /perfil  ->  el usuario dueño del token
@app.get("/perfil", response_model=UsuarioOut)
def perfil(token: dict = Depends(verificar_token), db: Session = Depends(get_db)):
    return buscar_o_404(db, token["id"])


# GET /usuarios  ->  todos
@app.get("/usuarios", response_model=list[UsuarioOut])
def listar(token: dict = Depends(verificar_token), db: Session = Depends(get_db)):
    return db.scalars(select(Usuario).order_by(Usuario.id)).all()


# GET /usuarios/{id}  ->  uno
@app.get("/usuarios/{id}", response_model=UsuarioOut)
def obtener(id: int, token: dict = Depends(verificar_token), db: Session = Depends(get_db)):
    return buscar_o_404(db, id)


# POST /usuarios  { correo, password, rol? }  ->  201 + usuario  (solo admin)
@app.post("/usuarios", response_model=UsuarioOut, status_code=201)
def crear(datos: UsuarioCrear, token: dict = Depends(solo_admin), db: Session = Depends(get_db)):
    if not datos.correo or not datos.password:
        raise HTTPException(status_code=400, detail="Faltan datos")
    if datos.rol and datos.rol not in ROLES:
        raise HTTPException(status_code=400, detail="Rol no válido")
    nuevo = Usuario(correo=datos.correo, password=datos.password, rol=datos.rol or "usuario")
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


# PUT /usuarios/{id}  { correo, password, rol }  ->  usuario actualizado  (solo admin)
@app.put("/usuarios/{id}", response_model=UsuarioOut)
def actualizar(
    id: int,
    datos: UsuarioActualizar,
    token: dict = Depends(solo_admin),
    db: Session = Depends(get_db),
):
    usuario = buscar_o_404(db, id)
    if datos.rol and datos.rol not in ROLES:
        raise HTTPException(status_code=400, detail="Rol no válido")
    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario


# DELETE /usuarios/{id}  ->  204 sin body  (solo admin)
@app.delete("/usuarios/{id}", status_code=204)
def borrar(id: int, token: dict = Depends(solo_admin), db: Session = Depends(get_db)):
    usuario = buscar_o_404(db, id)
    db.delete(usuario)
    db.commit()
    return Response(status_code=204)
