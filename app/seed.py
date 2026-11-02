# Crea la tabla (si falta) y crea o actualiza el admin inicial. Se puede correr varias veces.
# Uso: python -m app.seed
from sqlalchemy import select

from app.config import ADMIN_CORREO, ADMIN_PASSWORD
from app.database import Base, SessionLocal, engine
from app.models import Usuario


def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        admin = db.scalar(select(Usuario).where(Usuario.correo == ADMIN_CORREO))
        if admin:
            admin.password = ADMIN_PASSWORD
            admin.rol = "admin"
        else:
            admin = Usuario(correo=ADMIN_CORREO, password=ADMIN_PASSWORD, rol="admin")
            db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"Admin listo: {{ id: {admin.id}, correo: '{admin.correo}', rol: '{admin.rol}' }}")


if __name__ == "__main__":
    main()
