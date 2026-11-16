
from fastapi import FastAPI


from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.database import (
    obtener_productos_db,
    crear_tablas,
    crear_pedido
)
from pydantic import BaseModel, EmailStr, Field
from fastapi import HTTPException, status
from backend.database import registrar_usuario
from backend.security import crear_hash
from backend.database import buscar_usuario
from backend.security import verificar_password, crear_token
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.security import verificar_token
from backend.database import crear_pedido
import json
from backend.database import guardar_productos


app = FastAPI()
# Preparar las tablas de la base de datos
crear_tablas()

# Cargar productos iniciales si la base está vacía
ARCHIVO_PRODUCTOS = (
    Path(__file__).resolve().parent.parent
    / "productos_iniciales.json"
)

if ARCHIVO_PRODUCTOS.exists():
    with open(ARCHIVO_PRODUCTOS, "r", encoding="utf-8") as archivo:
        productos_iniciales = json.load(archivo)

    guardar_productos(productos_iniciales)


# Carpeta de videos situada junto a index.html
VIDEOS_DIR = Path(__file__).resolve().parent.parent / "videos"

app.mount(
    "/cafeteria/videos",
    StaticFiles(directory=str(VIDEOS_DIR)),
    name="cafe_videos"
)



@app.get("/")
def inicio():
    return {"mensaje": "¡Bienvenido al servidor de nuestra cafetería!"}


@app.get("/productos")
def obtener_productos():
    return obtener_productos_db()


FRONTEND = Path(__file__).resolve().parent.parent


@app.get("/cafeteria/")
def mostrar_cafeteria():
    return FileResponse(FRONTEND / "index.html")


@app.get("/cafeteria/style.css")
def obtener_estilos():
    return FileResponse(FRONTEND / "style.css")


@app.get("/cafeteria/script.js")
def obtener_javascript():
    return FileResponse(FRONTEND / "script.js")



class RegistroUsuario(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


@app.post("/registro", status_code=status.HTTP_201_CREATED)
def registro(datos: RegistroUsuario):
    password_hash = crear_hash(datos.password)

    usuario_id = registrar_usuario(
        nombre=datos.nombre.strip(),
        email=str(datos.email).lower(),
        password_hash=password_hash
    )

    if usuario_id is None:
        raise HTTPException(
            status_code=409,
            detail="Este correo ya está registrado"
        )

    return {
        "mensaje": "Usuario registrado correctamente",
        "usuario": {
            "id": usuario_id,
            "nombre": datos.nombre.strip(),
            "email": str(datos.email).lower()
        }
    }



class LoginUsuario(BaseModel):
    email: EmailStr
    password: str


@app.post("/login")
def login(datos: LoginUsuario):

  
    usuario = buscar_usuario(str(datos.email))


    if usuario is None or not verificar_password(
        datos.password,
        usuario["password_hash"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos"
        )


    token = crear_token(usuario["id"])

    return {
        "mensaje": "Inicio de sesión exitoso",
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id": usuario["id"],
            "nombre": usuario["nombre"],
            "email": usuario["email"],
            "rol": usuario["rol"]
        }
    }


# ========================================
# MODELOS PARA PEDIDOS - CAFÉ-OMEGA
# ========================================

class ProductoPedido(BaseModel):
    producto_id: int = Field(gt=0)
    cantidad: int = Field(ge=1, le=99)


class NuevoPedido(BaseModel):
    items: list[ProductoPedido] = Field(
        min_length=1,
        max_length=20
    )


# ==========================================
# AUTENTICACIÓN PARA PEDIDOS - CAFÉ-OMEGA
# ==========================================

seguridad_pedidos = HTTPBearer(auto_error=False)


def obtener_usuario_autenticado(
    credenciales: HTTPAuthorizationCredentials | None = Depends(
        seguridad_pedidos
    )
):
    if credenciales is None:
        raise HTTPException(
            status_code=401,
            detail="Debes iniciar sesión para realizar un pedido."
        )

    datos = verificar_token(credenciales.credentials)

    if not datos:
        raise HTTPException(
            status_code=401,
            detail="Tu sesión no es válida o ha expirado."
        )

    try:
        usuario_id = int(datos["sub"])

        if usuario_id <= 0:
            raise ValueError()

    except (KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="El token no contiene un usuario válido."
        )

    return usuario_id

# ==========================================
# CREAR PEDIDOS - CAFÉ-OMEGA
# ==========================================

@app.post("/pedidos", status_code=201)
def registrar_pedido(
    pedido: NuevoPedido,
    usuario_id: int = Depends(obtener_usuario_autenticado)
):
    try:
        resultado = crear_pedido(
            usuario_id=usuario_id,
            items=[
                item.model_dump()
                for item in pedido.items
            ]
        )

        return {
            "mensaje": "¡Pedido registrado correctamente!",
            **resultado
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
