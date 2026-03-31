import os
import sys

# Asegurar que el directorio raíz está en el PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.db.database import init_db
from src.ui.app import main_app
from src.services.watcher import stop_watcher

def start():
    print("Iniciando SDGF...")
    
    # 1. Asegurar Backend DB
    init_db()
    print("Base de datos inicializada")
    
    # 2. Iniciar UI (que a su vez arranca el Watcher)
    try:
        main_app()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error crítico en Flet: {e}")
    finally:
        # 3. Limpieza al cerrar la ventana del navegador
        stop_watcher()
        print("SDGF cerrado.")

if __name__ == "__main__":
    start()
