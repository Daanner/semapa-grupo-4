from pathlib import Path
import sys

# Permite inicializar la base sin levantar Flask.
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "app"))

from app.db.repository import seed_db

if __name__ == "__main__":
    result = seed_db(force=True)
    print("Base de datos SEMAPA inicializada correctamente")
    print(result)
