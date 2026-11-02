# Forma del JSON que entra y sale (Pydantic).
from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    correo: str | None = None
    password: str | None = None


class TokenResponse(BaseModel):
    token: str


class UsuarioCrear(BaseModel):
    correo: str | None = None
    password: str | None = None
    rol: str | None = None


class UsuarioActualizar(BaseModel):
    # Solo se actualizan los campos que vengan en el body.
    correo: str | None = None
    password: str | None = None
    rol: str | None = None


class UsuarioOut(BaseModel):
    # Lo que responde la API: NUNCA incluye el password.
    model_config = ConfigDict(from_attributes=True)

    id: int
    correo: str
    rol: str
