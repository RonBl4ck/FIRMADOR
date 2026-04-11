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


class GoogleDriveStorage(StorageBackend):
    def __init__(self) -> None:
        import streamlit as st
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        token_data = dict(st.secrets["gcp_oauth"])
        creds = Credentials(
            token=token_data["token"],
            refresh_token=token_data["refresh_token"],
            token_uri=token_data["token_uri"],
            client_id=token_data["client_id"],
            client_secret=token_data["client_secret"]
        )
        
        self.service = build('drive', 'v3', credentials=creds)
        self.base_folder_name = "SSUU CARTAS"
        self.folder_map = {
            "entrada": "POR FIRMAR",
            "firmados": "FIRMADO"
        }
        self.mapped_ids = {} # logical folder config (e.g. 'entrada') -> google drive folder id
        self.root_folder_id = None
        self.ensure_structure()

    def ensure_structure(self) -> None:
        # Buscar SSUU CARTAS
        query = f"name='{self.base_folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        
        if not items:
            # Crearla
            file_metadata = {
                'name': self.base_folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            self.root_folder_id = folder.get('id')
        else:
            self.root_folder_id = items[0].get('id')

        # Buscar o crear subcarpetas
        for key, name in self.folder_map.items():
            query = f"name='{name}' and '{self.root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            res = self.service.files().list(q=query, fields="files(id, name)").execute()
            sub_items = res.get('files', [])
            if not sub_items:
                file_metadata = {
                    'name': name,
                    'parents': [self.root_folder_id],
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                sub = self.service.files().create(body=file_metadata, fields='id').execute()
                self.mapped_ids[key] = sub.get('id')
            else:
                self.mapped_ids[key] = sub_items[0].get('id')

    def upload(self, folder: str, filename: str, content: bytes) -> StoredFile:
        from googleapiclient.http import MediaIoBaseUpload
        import io
        
        parent_id = self.mapped_ids.get(folder)
        if not parent_id:
            raise ValueError(f"Carpeta no configurada: {folder}")
            
        file_metadata = {
            'name': filename,
            'parents': [parent_id]
        }
        media = MediaIoBaseUpload(io.BytesIO(content), mimetype='application/pdf', resumable=True)
        file = self.service.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
        return StoredFile(name=file.get('name'), path=f"{folder}/{file.get('name')}", storage_id=file.get('id'))

    def copy_between(self, source_path: str, target_folder: str, target_name: Optional[str] = None) -> StoredFile:
        # Implementar como descarga temporal local + subida para Google Drive MVP
        filename = target_name or source_path.replace("\\", "/").split('/')[-1]
        content = self.read_bytes(source_path)
        return self.upload(target_folder, filename, content)

    def move_between(self, source_path: str, target_folder: str, target_name: Optional[str] = None) -> StoredFile:
        # Buscar e ID para mover por API PATCH
        filename = source_path.replace("\\", "/").split('/')[-1]
        
        # Inferir parent de source
        source_logical_folder = source_path.split('/')[0] if '/' in source_path else "entrada"
        source_parent_id = self.mapped_ids.get(source_logical_folder, self.mapped_ids.get("entrada"))
        target_parent_id = self.mapped_ids.get(target_folder)
        
        if not target_parent_id:
            raise ValueError(f"Carpeta destino no configurada: {target_folder}")

        query = f"name='{filename}' and '{source_parent_id}' in parents and trashed=false"
        res = self.service.files().list(q=query, fields="files(id, parents)").execute()
        items = res.get('files', [])
        if not items:
            raise FileNotFoundError(f"Archivo origenn no encontrado en drive: {source_path}")
            
        file_id = items[0].get('id')
        previous_parents = ",".join(items[0].get('parents'))
        
        file_metadata = {}
        if target_name:
            file_metadata['name'] = target_name
            
        file = self.service.files().update(
            fileId=file_id,
            addParents=target_parent_id,
            removeParents=previous_parents,
            body=file_metadata,
            fields='id, name'
        ).execute()
        return StoredFile(name=file.get('name'), path=f"{target_folder}/{file.get('name')}", storage_id=file.get('id'))

    def read_bytes(self, path: str) -> bytes:
        import io
        from googleapiclient.http import MediaIoBaseDownload
        
        filename = path.replace("\\", "/").split('/')[-1]
        logical_folder = path.split('/')[0] if '/' in path else "entrada"
        parent_id = self.mapped_ids.get(logical_folder, self.mapped_ids.get("entrada"))
        
        query = f"name='{filename}' and '{parent_id}' in parents and trashed=false"
        res = self.service.files().list(q=query, fields="files(id)").execute()
        items = res.get('files', [])
        if not items:
            raise FileNotFoundError(f"Archivo no encontrado: {path}")
            
        file_id = items[0].get('id')
        request = self.service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        return file_io.getvalue()

    def exists(self, path: str) -> bool:
        filename = path.replace("\\", "/").split('/')[-1]
        logical_folder = path.split('/')[0] if '/' in path else "entrada"
        parent_id = self.mapped_ids.get(logical_folder, self.mapped_ids.get("entrada"))
        query = f"name='{filename}' and '{parent_id}' in parents and trashed=false"
        res = self.service.files().list(q=query, fields="files(id)").execute()
        return len(res.get('files', [])) > 0


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
    mode = (ConfigService.get("storage_mode", "google_drive") or "google_drive").strip().lower()
    if mode == "onedrive_api":
        return OneDriveApiStorage()
    elif mode == "google_drive":
        return GoogleDriveStorage()
    return LocalFolderStorage()
