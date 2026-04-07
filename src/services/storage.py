import os
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional

from src.db.models import ConfigService


DEFAULT_BASE = Path("C:/Gestion_Firmas/streamlit_storage")
DEFAULT_INBOX = DEFAULT_BASE / "entrada"
DEFAULT_SIGNED = DEFAULT_BASE / "firmados"
DEFAULT_REJECTED = DEFAULT_BASE / "rechazados"
DEFAULT_TEMP = DEFAULT_BASE / "temp"


@dataclass
class StoredFile:
    name: str
    path: str
    storage_id: Optional[str] = None


class StorageBackend(ABC):
    @abstractmethod
    def upload(self, folder: str, filename: str, content: bytes) -> StoredFile:
        raise NotImplementedError

    @abstractmethod
    def copy_between(self, source_path: str, target_folder: str, target_name: Optional[str] = None) -> StoredFile:
        raise NotImplementedError

    @abstractmethod
    def move_between(self, source_path: str, target_folder: str, target_name: Optional[str] = None) -> StoredFile:
        raise NotImplementedError

    @abstractmethod
    def read_bytes(self, path: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def exists(self, path: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def ensure_structure(self) -> None:
        raise NotImplementedError


class LocalFolderStorage(StorageBackend):
    def __init__(self) -> None:
        self.base_dir = Path(ConfigService.get("storage_local_base_dir", str(DEFAULT_BASE)))
        self.folder_map = {
            "entrada": Path(ConfigService.get("storage_local_inbox_dir", str(DEFAULT_INBOX))),
            "firmados": Path(ConfigService.get("storage_local_signed_dir", str(DEFAULT_SIGNED))),
            "rechazados": Path(ConfigService.get("storage_local_rejected_dir", str(DEFAULT_REJECTED))),
            "temp": Path(ConfigService.get("storage_local_temp_dir", str(DEFAULT_TEMP))),
        }
        self.ensure_structure()

    def ensure_structure(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for folder in self.folder_map.values():
            folder.mkdir(parents=True, exist_ok=True)

    def upload(self, folder: str, filename: str, content: bytes) -> StoredFile:
        target = self._resolve_file(folder, filename)
        target.write_bytes(content)
        return StoredFile(name=target.name, path=str(target))

    def copy_between(self, source_path: str, target_folder: str, target_name: Optional[str] = None) -> StoredFile:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"No existe el archivo origen: {source}")
        target = self._resolve_file(target_folder, target_name or source.name)
        shutil.copy2(source, target)
        return StoredFile(name=target.name, path=str(target))

    def move_between(self, source_path: str, target_folder: str, target_name: Optional[str] = None) -> StoredFile:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"No existe el archivo origen: {source}")
        target = self._resolve_file(target_folder, target_name or source.name)
        shutil.move(str(source), str(target))
        return StoredFile(name=target.name, path=str(target))

    def read_bytes(self, path: str) -> bytes:
        return Path(path).read_bytes()

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def _resolve_file(self, folder: str, filename: str) -> Path:
        if folder not in self.folder_map:
            raise ValueError(f"Carpeta de almacenamiento no soportada: {folder}")
        return self.folder_map[folder] / filename


class OneDriveApiStorage(StorageBackend):
    """
    Adaptador listo para conectar mañana con Microsoft Graph.
    Por ahora falla de forma explícita para no mezclar estados falsos.
    """

    def ensure_structure(self) -> None:
        return

    def upload(self, folder: str, filename: str, content: bytes) -> StoredFile:
        raise NotImplementedError("OneDrive API aún no está conectada. Usa modo local o implementa este adaptador.")

    def copy_between(self, source_path: str, target_folder: str, target_name: Optional[str] = None) -> StoredFile:
        raise NotImplementedError("OneDrive API aún no está conectada. Usa modo local o implementa este adaptador.")

    def move_between(self, source_path: str, target_folder: str, target_name: Optional[str] = None) -> StoredFile:
        raise NotImplementedError("OneDrive API aún no está conectada. Usa modo local o implementa este adaptador.")

    def read_bytes(self, path: str) -> bytes:
        raise NotImplementedError("OneDrive API aún no está conectada. Usa modo local o implementa este adaptador.")

    def exists(self, path: str) -> bool:
        raise NotImplementedError("OneDrive API aún no está conectada. Usa modo local o implementa este adaptador.")


def get_storage_backend() -> StorageBackend:
    mode = (ConfigService.get("storage_mode", "local") or "local").strip().lower()
    if mode == "onedrive_api":
        return OneDriveApiStorage()
    return LocalFolderStorage()
