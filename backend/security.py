
import os
import jwt

from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

# Cargar las variables privadas desde .env
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "Falta JWT_SECRET_KEY o es demasiado corta en .env"
    )

ALGORITHM = "HS256"
TOKEN_DURATION = 60  # Minutos

# Protección de contraseñas
password_hasher = PasswordHasher()


def crear_hash(password: str) -> str:
    return password_hasher.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False


# Crear un token al iniciar sesión
def crear_token(usuario_id: int) -> str:
    expiracion = datetime.now(timezone.utc) + timedelta(
        minutes=TOKEN_DURATION
    )

    datos = {
        "sub": str(usuario_id),
        "exp": expiracion
    }

    return jwt.encode(
        datos,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# Verificar un token
def verificar_token(token: str):
    try:
        return jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except jwt.InvalidTokenError:
        return None
