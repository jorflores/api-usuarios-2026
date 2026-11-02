# Lee la configuración de las variables de entorno (o del archivo .env en local).
import os
import sys

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")
ADMIN_CORREO = os.getenv("ADMIN_CORREO", "admin@mail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")

if not DATABASE_URL or not JWT_SECRET:
    sys.exit("Faltan variables de entorno: DATABASE_URL y JWT_SECRET (revisa tu .env)")
