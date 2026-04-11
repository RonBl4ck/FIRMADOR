import csv
from pathlib import Path
from typing import Dict, Iterable

from src.db.models import ConfigService


DEFAULT_REGISTRY_PATH = Path("C:/Gestion_Firmas/streamlit_storage/registro_operativo.csv")


class GoogleSheetsRegistry:
    def __init__(self):
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
        
        self.sheets_service = build('sheets', 'v4', credentials=creds)
        self.drive_service = build('drive', 'v3', credentials=creds)
        self.spreadsheet_id = None
        self.base_folder_name = "SSUU CARTAS"
        self.sheet_name = "Registro Operativo"
        self.ensure_sheet()

    def ensure_sheet(self):
        # 1. Buscar carpeta SSUU CARTAS
        query = f"name='{self.base_folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        if not items:
            print("Esperando que SSUU CARTAS sea creada por Storage...")
            return 
        folder_id = items[0].get('id')
        
        # 2. Buscar spreadsheet
        file_name = "Registro_Operativo_SSUU"
        query = f"name='{file_name}' and '{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
        res = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
        s_items = res.get('files', [])
        
        if not s_items:
            # Create
            spreadsheet_body = {
                'properties': {
                    'title': file_name
                }
            }
            request = self.sheets_service.spreadsheets().create(body=spreadsheet_body, fields='spreadsheetId')
            response = request.execute()
            self.spreadsheet_id = response.get('spreadsheetId')
            
            # Mover a la carpeta usando PATCH (update)
            self.drive_service.files().update(
                fileId=self.spreadsheet_id,
                addParents=folder_id,
                fields='id, parents'
            ).execute()
            
            self._write_headers()
        else:
            self.spreadsheet_id = s_items[0].get('id')

    def _write_headers(self):
        headers = ["id", "nombre_archivo", "estado", "remitente", "destinatario", "fecha_envio", "fecha_recibo", "fecha_firma", "ruta_original", "ruta_backup", "observaciones"]
        body = {
            'values': [headers]
        }
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"A1:K1",
            valueInputOption="RAW",
            body=body
        ).execute()

    def sync(self, rows):
        if not self.spreadsheet_id:
            self.ensure_sheet()
            if not self.spreadsheet_id:
                return # Still no folder available
                
        headers = ["id", "nombre_archivo", "estado", "remitente", "destinatario", "fecha_envio", "fecha_recibo", "fecha_firma", "ruta_original", "ruta_backup", "observaciones"]
        
        values = [headers]
        for row in rows:
            values.append([row.get(k, "") for k in headers])
            
        # Limpiar existente
        self.sheets_service.spreadsheets().values().clear(
            spreadsheetId=self.spreadsheet_id,
            range="A:K"
        ).execute()
        
        # Actualizar
        body = {
            'values': values
        }
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range="A1",
            valueInputOption="RAW",
            body=body
        ).execute()

def _registry_mode() -> str:
    return (ConfigService.get("registry_mode", "google_sheets") or "google_sheets").strip().lower()


def sync_registry(rows: Iterable[Dict]) -> None:
    mode = _registry_mode()
    if mode == "disabled":
        return
    if mode in {"csv", "excel_local"}:
        _write_csv(rows)
        return
    if mode in {"google_drive", "google_sheets"}:
        GoogleSheetsRegistry().sync(list(rows))
        return
    _write_csv(rows)


def _write_csv(rows: Iterable[Dict]) -> None:
    target = Path(ConfigService.get("registry_csv_path", str(DEFAULT_REGISTRY_PATH)))
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    fieldnames = [
        "id",
        "nombre_archivo",
        "estado",
        "remitente",
        "destinatario",
        "fecha_envio",
        "fecha_recibo",
        "fecha_firma",
        "ruta_original",
        "ruta_backup",
        "observaciones",
    ]
    with target.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
