# Seguridad con JWT: equivalentes de verificarToken y soloAdmin.
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request

from app.config import JWT_SECRET

ALGORITMO = "HS256"


def crear_token(usuario_id: int, rol: str) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {"id": usuario_id, "rol": rol, "iat": ahora, "exp": ahora + timedelta(hours=1)}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITMO)


def verificar_token(request: Request) -> dict:
    """Revisa el gafete: ¿la petición trae un token válido? Regresa el payload { id, rol }."""
    header = request.headers.get("Authorization")
    if not header:
        raise HTTPException(status_code=401, detail="Falta el token")
    partes = header.split(" ")  # "Bearer eyJ..." -> ["Bearer", "eyJ..."]
    token = partes[1] if len(partes) > 1 else ""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITMO])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token no válido")


def solo_admin(usuario: dict = Depends(verificar_token)) -> dict:
    """Va DESPUÉS de verificar_token: ya sabemos quién es, ¿puede hacerlo?"""
    if usuario.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Solo un admin puede hacer esto")
    return usuario
