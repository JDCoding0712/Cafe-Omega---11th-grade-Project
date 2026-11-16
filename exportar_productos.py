
import json
from pathlib import Path
from backend.database import obtener_productos_db

productos = obtener_productos_db()

archivo = Path(__file__).resolve().parent / "productos_iniciales.json"

archivo.write_text(
    json.dumps(productos, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"✅ Se exportaron {len(productos)} productos.")
print("Archivo creado:", archivo.name)
