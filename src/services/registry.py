import csv
from pathlib import Path
from typing import Dict, Iterable

from src.db.models import ConfigService


DEFAULT_REGISTRY_PATH = Path("C:/Gestion_Firmas/streamlit_storage/registro_operativo.csv")


def _registry_mode() -> str:
    return (ConfigService.get("registry_mode", "csv") or "csv").strip().lower()


def sync_registry(rows: Iterable[Dict]) -> None:
    mode = _registry_mode()
    if mode == "disabled":
        return
    if mode in {"csv", "excel_local"}:
        _write_csv(rows)
        return
    if mode in {"excel_online", "google_sheets"}:
        # Punto de extensión para mañana.
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
