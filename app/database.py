# Conexión a PostgreSQL con SQLAlchemy.
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL


def _url_para_sqlalchemy(url: str) -> str:
    # Render y Docker dan "postgresql://..."; SQLAlchemy con psycopg 3 usa "postgresql+psycopg://...".
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    # "no-verify" es de Node; en Python el equivalente es "require" (cifra sin validar el certificado).
    return url.replace("sslmode=no-verify", "sslmode=require")


engine = create_engine(_url_para_sqlalchemy(DATABASE_URL), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    # Una sesión por petición; se cierra al terminar.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
