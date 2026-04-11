import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.services.storage import GoogleDriveStorage

def test():
    try:
        storage = GoogleDriveStorage()
        storage.upload("entrada", "test_file.txt", b"hola mundo")
        print("Upload exitoso.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
