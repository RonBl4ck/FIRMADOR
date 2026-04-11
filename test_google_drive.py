import os
import sys

# Asegurar que el directorio raíz está en el PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.services.storage import GoogleDriveStorage
from src.services.registry import GoogleSheetsRegistry

def test_drive():
    try:
        print("Iniciando prueba de Google Drive Storage...")
        storage = GoogleDriveStorage()
        print(f"Estructura asegurada. Root Folder ID: {storage.root_folder_id}")
        print(f"Carpetas mapeadas: {storage.mapped_ids}")
        
        print("\nIniciando prueba de Google Sheets...")
        registry = GoogleSheetsRegistry()
        print(f"Spreadsheet ID: {registry.spreadsheet_id}")
        
        print("\nSincronizando un registro de prueba...")
        rows = [
            {"id": "1", "nombre_archivo": "test.pdf", "estado": "prueba_conexion"}
        ]
        registry.sync(rows)
        print("Prueba completada con éxito.")
    except Exception as e:
        print(f"Error durante la prueba: {e}")

if __name__ == "__main__":
    test_drive()
