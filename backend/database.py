
import sqlite3
from pathlib import Path

DATABASE = Path(__file__).resolve().parent / "cafeteria.db"


def conectar():
    conexion = sqlite3.connect(DATABASE)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def crear_tablas():
    with conectar() as conexion:

        # Tabla de productos
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price INTEGER NOT NULL CHECK(price >= 0),
                description TEXT NOT NULL,
                image TEXT NOT NULL
            )
        """)

        # Tabla de usuarios
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'cliente'
                    CHECK(rol IN ('cliente', 'admin'))
            )
        """)

        # Tabla de pedidos
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                total INTEGER NOT NULL CHECK(total >= 0),
                estado TEXT NOT NULL DEFAULT 'pendiente',
                fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)

        # Productos incluidos en cada pedido
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS detalle_pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                nombre_producto TEXT NOT NULL,
                cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                precio_unitario INTEGER NOT NULL CHECK(precio_unitario >= 0),
                subtotal INTEGER NOT NULL CHECK(subtotal >= 0),
                FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        """)


def guardar_productos(productos):
    with conectar() as conexion:
        for producto in productos:
            conexion.execute("""
                INSERT OR IGNORE INTO productos
                (id, name, category, price, description, image)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                producto["id"],
                producto["name"],
                producto["category"],
                producto["price"],
                producto["description"],
                producto["image"]
            ))


def obtener_productos_db():
    conexion = conectar()

    try:
        cursor = conexion.execute(
            "SELECT * FROM productos ORDER BY id"
        )

        productos = [
            dict(fila) for fila in cursor.fetchall()
        ]

        return productos

    finally:
        conexion.close()


def registrar_usuario(nombre, email, password_hash):
    try:
        with conectar() as conexion:
            cursor = conexion.execute("""
                INSERT INTO usuarios (nombre, email, password_hash)
                VALUES (?, ?, ?)
            """, (nombre, email, password_hash))

            return cursor.lastrowid

    except sqlite3.IntegrityError:
        return None


# Buscar una cuenta por su correo
def buscar_usuario(email):
    conexion = conectar()

    try:
        cursor = conexion.execute("""
            SELECT id, nombre, email, password_hash, rol
            FROM usuarios
            WHERE email = ?
        """, (email.strip().lower(),))

        usuario = cursor.fetchone()

        return dict(usuario) if usuario else None

    finally:
        conexion.close()


# ==========================================
# SISTEMA DE PEDIDOS - CAFÉ-OMEGA
# ==========================================

def crear_pedido(usuario_id, items):
    """
    Guarda un pedido y sus productos en SQLite.

    items debe tener este formato:
    [
        {"producto_id": 1, "cantidad": 2},
        {"producto_id": 3, "cantidad": 1}
    ]

    Los precios se obtienen de SQLite,
    no del navegador del cliente.
    """

    if not isinstance(items, list) or not (1 <= len(items) <= 20):
        raise ValueError("El pedido debe contener entre 1 y 20 productos.")

    conexion = conectar()

    try:
        with conexion:

            # Verificar que el cliente exista
            usuario = conexion.execute(
                "SELECT id FROM usuarios WHERE id = ?",
                (usuario_id,)
            ).fetchone()

            if usuario is None:
                raise ValueError("El usuario no existe.")

            detalles = []
            total = 0

            for item in items:
                producto_id = item.get("producto_id")
                cantidad = item.get("cantidad")

                if (
                    type(producto_id) is not int
                    or type(cantidad) is not int
                    or not (1 <= cantidad <= 99)
                ):
                    raise ValueError(
                        "El producto o la cantidad no son válidos."
                    )

                producto = conexion.execute("""
                    SELECT id, name, price
                    FROM productos
                    WHERE id = ?
                """, (producto_id,)).fetchone()

                if producto is None:
                    raise ValueError(
                        f"No existe el producto {producto_id}."
                    )

                subtotal = producto["price"] * cantidad
                total += subtotal

                detalles.append({
                    "producto_id": producto["id"],
                    "nombre": producto["name"],
                    "cantidad": cantidad,
                    "precio": producto["price"],
                    "subtotal": subtotal
                })

            # Guardar el pedido principal
            cursor = conexion.execute("""
                INSERT INTO pedidos (usuario_id, total)
                VALUES (?, ?)
            """, (usuario_id, total))

            pedido_id = cursor.lastrowid

            # Guardar los productos del pedido
            for detalle in detalles:
                conexion.execute("""
                    INSERT INTO detalle_pedidos (
                        pedido_id,
                        producto_id,
                        nombre_producto,
                        cantidad,
                        precio_unitario,
                        subtotal
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    pedido_id,
                    detalle["producto_id"],
                    detalle["nombre"],
                    detalle["cantidad"],
                    detalle["precio"],
                    detalle["subtotal"]
                ))

            return {
                "pedido_id": pedido_id,
                "total": total,
                "estado": "pendiente"
            }

    finally:
        conexion.close()
