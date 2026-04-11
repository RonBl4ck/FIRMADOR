import datetime
import os
import re
from typing import Dict, List, Optional

from src.db.database import get_db_connection
from src.db.models import ConfigService, DocumentoService, HistorialService
from src.pdf.signer import proceso_firma_completa
from src.services.registry import sync_registry
from src.services.storage import get_storage_backend


USER_MAP = {
    "a": {"nombre": "A", "rol": "emisor"},
    "martin": {"nombre": "Martin", "rol": "firmante"},
}


def ensure_streamlit_config() -> None:
    defaults = {
        "storage_mode": "local",
        "registry_mode": "csv",
        "app_default_profile": "a",
        "firma_path": "C:/Gestion_Firmas/firma.png",
        "pfx_path": "",
        "pfx_pass": "",
    }
    for key, value in defaults.items():
        if ConfigService.get(key) is None:
            ConfigService.set(key, value)
    get_storage_backend().ensure_structure()


def get_profiles() -> List[str]:
    return list(USER_MAP.keys())


def get_profile_meta(profile: str) -> Dict[str, str]:
    return USER_MAP.get(profile, {"nombre": profile.title(), "rol": "emisor"})


def submit_document(
    *,
    filename: str,
    content: bytes,
    category: str,
    uploaded_by: str,
    atc_code: str,
    decision_type: str,
    signature_position: Optional[Dict[str, float]] = None,
    destinatario: str = "Martin",
    notes: str = "",
) -> int:
    backend = get_storage_backend()
    ensure_streamlit_config()

    final_name = build_document_filename(
        original_filename=filename,
        atc_code=atc_code,
        decision_type=decision_type,
    )

    stored = backend.upload("entrada", final_name, content)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    doc_id = DocumentoService.agregar_documento(
        nombre=final_name,
        ruta_original=stored.path,
        remitente=uploaded_by,
        destinatario=destinatario,
        estado="enviado",
        categoria=category or "General",
        rol_origen="emisor",
        fecha_envio=now,
        fecha_recibo=now,
    )
    if notes:
        update_document_notes(doc_id, notes)
    if signature_position:
        update_signature_position(doc_id, signature_position)
    HistorialService.log(doc_id, "Documento enviado a bandeja de firma", uploaded_by, details_or_blank(notes))
    refresh_registry_snapshot()
    return doc_id


def get_documents_for_profile(profile: str) -> List[Dict]:
    role = get_profile_meta(profile)["rol"]
    docs = DocumentoService.get_all(role)
    if role == "firmante":
        return [doc for doc in docs if doc["estado"] == "enviado"]
    return docs


def get_all_documents() -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documentos ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_history(limit: int = 100) -> List[Dict]:
    return HistorialService.get_recent(limit)


def sign_document(doc_id: int, actor: str) -> str:
    doc = DocumentoService.get_by_id(doc_id)
    if not doc:
        raise ValueError("Documento no encontrado.")
    if doc["estado"] != "enviado":
        raise ValueError("Solo se pueden firmar documentos en estado enviado.")
    page_index = int(doc["firma_pagina"]) if doc.get("firma_pagina") is not None else None

    firma_path = ConfigService.get("firma_path", "C:/Gestion_Firmas/firma.png")
    pfx_path = ConfigService.get("pfx_path", "")
    pfx_pass = ConfigService.get("pfx_pass", "")

    if not os.path.exists(doc["ruta_original"]):
        raise FileNotFoundError(f"No se encontró el PDF original: {doc['ruta_original']}")

    signed_path = proceso_firma_completa(
        doc["ruta_original"],
        firma_path,
        "C:/Gestion_Firmas/Backup",
        pfx_path=pfx_path,
        pfx_pass=pfx_pass,
        page_index=page_index,
        x=_coalesce_float(doc.get("firma_x"), default=300),
        y=_coalesce_float(doc.get("firma_y"), default=100),
        width=_coalesce_float(doc.get("firma_w"), default=150),
        height=_coalesce_float(doc.get("firma_h"), default=80),
    )
    backend = get_storage_backend()
    signed_name = os.path.basename(signed_path)
    with open(signed_path, "rb") as signed_file:
        stored = backend.upload("firmados", signed_name, signed_file.read())

    DocumentoService.actualizar_estado(doc_id, "firmado", stored.path)
    HistorialService.log(doc_id, "Documento firmado", actor, f"Salida: {stored.path}")
    refresh_registry_snapshot()
    return stored.path


def reject_document(doc_id: int, actor: str, reason: str) -> None:
    doc = DocumentoService.get_by_id(doc_id)
    if not doc:
        raise ValueError("Documento no encontrado.")
    if doc["estado"] != "enviado":
        raise ValueError("Solo se pueden rechazar documentos en estado enviado.")

    backend = get_storage_backend()
    rejected_name = _suffix_filename(doc["nombre_archivo"], "_rechazado")
    stored = backend.copy_between(doc["ruta_original"], "rechazados", rejected_name)
    update_document_notes(doc_id, reason)
    DocumentoService.actualizar_estado(doc_id, "rechazado", stored.path)
    HistorialService.log(doc_id, "Documento rechazado", actor, details_or_blank(reason))
    refresh_registry_snapshot()


def save_signature_file(content: bytes, filename: str) -> str:
    path = Path("assets/credentials")
    path.mkdir(parents=True, exist_ok=True)
    target = path / filename
    target.write_bytes(content)
    ConfigService.set("firma_path", str(target.absolute()))
    return str(target.absolute())


def save_pfx_file(content: bytes, filename: str) -> str:
    path = Path("assets/credentials")
    path.mkdir(parents=True, exist_ok=True)
    target = path / filename
    target.write_bytes(content)
    ConfigService.set("pfx_path", str(target.absolute()))
    return str(target.absolute())


def update_settings(settings: Dict[str, str]) -> None:
    for key, value in settings.items():
        ConfigService.set(key, value)
    ensure_streamlit_config()


def get_settings() -> Dict[str, str]:
    keys = [
        "storage_mode",
        "storage_local_base_dir",
        "storage_local_inbox_dir",
        "storage_local_signed_dir",
        "storage_local_rejected_dir",
        "storage_local_temp_dir",
        "registry_mode",
        "registry_csv_path",
        "firma_path",
        "pfx_path",
        "pfx_pass",
        "onedrive_tenant_id",
        "onedrive_client_id",
        "onedrive_client_secret",
        "onedrive_drive_id",
        "onedrive_folder_inbox",
        "onedrive_folder_signed",
        "onedrive_folder_rejected",
    ]
    return {key: ConfigService.get(key, "") for key in keys}


def refresh_registry_snapshot() -> None:
    sync_registry(get_all_documents())


def update_document_notes(doc_id: int, notes: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE documentos SET observaciones = ? WHERE id = ?", (notes, doc_id))
    conn.commit()
    conn.close()


def update_signature_position(doc_id: int, signature_position: Dict[str, float]) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE documentos
        SET firma_pagina = ?, firma_x = ?, firma_y = ?, firma_w = ?, firma_h = ?
        WHERE id = ?
        """,
        (
            int(signature_position["page_index"]),
            float(signature_position["x"]),
            float(signature_position["y"]),
            float(signature_position["width"]),
            float(signature_position["height"]),
            doc_id,
        ),
    )
    conn.commit()
    conn.close()


def details_or_blank(text: Optional[str]) -> str:
    return (text or "").strip()


def _suffix_filename(filename: str, suffix: str) -> str:
    base, ext = os.path.splitext(filename)
    return f"{base}{suffix}{ext or '.pdf'}"


def build_document_filename(original_filename: str, atc_code: str, decision_type: str) -> str:
    safe_name = _slugify_filename_part(os.path.splitext(os.path.basename(original_filename))[0])
    atc = _slugify_filename_part(atc_code.upper())
    status_code = _decision_code(decision_type)
    year = datetime.datetime.now().year
    return f"PD-{atc}-{status_code}-{year}_{safe_name}.pdf"


def _decision_code(decision_type: str) -> str:
    normalized = (decision_type or "").strip().lower()
    return "A" if normalized == "aprobado" else "O"


def _slugify_filename_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "SIN_DATO"


def _coalesce_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)

