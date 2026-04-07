import io
import os
import sys
from typing import Dict, List, Optional

import streamlit as st
from PIL import Image, ImageDraw
from PyPDF2 import PdfReader


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    import fitz
except ImportError:
    fitz = None

from src.db.database import init_db
from src.services.storage import get_storage_backend
from src.services.workflow import (
    build_document_filename,
    ensure_streamlit_config,
    get_all_documents,
    get_documents_for_profile,
    get_history,
    get_profile_meta,
    get_profiles,
    get_settings,
    refresh_registry_snapshot,
    reject_document,
    sign_document,
    submit_document,
    update_settings,
)


def run() -> None:
    init_db()
    ensure_streamlit_config()
    st.set_page_config(page_title="SDGF Streamlit", page_icon=":page_facing_up:", layout="wide")
    _render_sidebar()

    page = st.session_state.get("page", "panel")
    profile = st.session_state.get("profile", "a")

    st.title("SDGF")
    st.caption("Flujo de envio, firma y rechazo preparado para OneDrive API o almacenamiento local.")

    if page == "panel":
        _render_panel(profile)
    elif page == "historial":
        _render_history()
    else:
        _render_settings()


def _render_sidebar() -> None:
    with st.sidebar:
        st.header("Sesion")
        profiles = get_profiles()
        selected_profile = st.selectbox(
            "Perfil",
            options=profiles,
            format_func=lambda key: get_profile_meta(key)["nombre"],
            index=profiles.index(st.session_state.get("profile", "a")) if st.session_state.get("profile", "a") in profiles else 0,
        )
        st.session_state["profile"] = selected_profile

        page_labels = {
            "panel": "Panel",
            "historial": "Historial",
            "configuracion": "Configuracion",
        }
        selected_page = st.radio(
            "Ir a",
            options=list(page_labels.keys()),
            format_func=lambda key: page_labels[key],
            index=list(page_labels.keys()).index(st.session_state.get("page", "panel")),
        )
        st.session_state["page"] = selected_page

        st.divider()
        if st.button("Actualizar registro", use_container_width=True):
            refresh_registry_snapshot()
            st.success("Registro sincronizado.")


def _render_panel(profile: str) -> None:
    if get_profile_meta(profile)["rol"] == "firmante":
        _render_firmante_panel(profile)
    else:
        _render_emisor_panel(profile)


def _render_emisor_panel(profile: str) -> None:
    st.subheader("Panel Emisor")
    left, right = st.columns([1.05, 1.35], gap="large")

    with left:
        st.markdown("### Enviar PDF")
        uploaded = st.file_uploader("PDF sin firmar", type=["pdf"])
        decision_type = st.selectbox("Tipo", ["Aprobado", "Observado"])
        atc_code = st.text_input("ATC", placeholder="Ejemplo: ATC123 o 015")
        category = st.selectbox("Categoria", ["Contrato", "Carta", "Memorandum", "Otro"])
        notes = st.text_area("Observaciones", placeholder="Detalle opcional para Martin")

        signature_position = None
        if uploaded:
            signature_position = _render_signature_selector(uploaded)

        if uploaded and atc_code.strip():
            preview_name = build_document_filename(
                original_filename=uploaded.name,
                atc_code=atc_code,
                decision_type=decision_type,
            )
            st.caption(f"Nombre final: `{preview_name}`")

        if st.button("Enviar a firma", type="primary", use_container_width=True):
            if not uploaded:
                st.error("Selecciona un PDF antes de enviar.")
            elif not atc_code.strip():
                st.error("Ingresa la ATC antes de enviar.")
            elif not signature_position:
                st.error("Define primero la zona de firma.")
            else:
                doc_id = submit_document(
                    filename=uploaded.name,
                    content=uploaded.getvalue(),
                    category=category,
                    uploaded_by=get_profile_meta(profile)["nombre"],
                    atc_code=atc_code,
                    decision_type=decision_type,
                    signature_position=signature_position,
                    notes=notes,
                )
                st.success(f"Documento enviado. ID {doc_id}.")

    with right:
        st.markdown("### Mis documentos")
        docs = get_documents_for_profile(profile)
        _render_documents_table(docs)
        _render_download_section(docs, title="Abrir o descargar firmado")


def _render_signature_selector(uploaded) -> Optional[Dict[str, float]]:
    pdf_bytes = uploaded.getvalue()
    metadata = _get_pdf_metadata(pdf_bytes)
    if not metadata["pages"]:
        st.warning("No se pudo leer el PDF para definir la firma.")
        return None

    st.markdown("### Zona de firma")
    page_options = [f"Pagina {page['index'] + 1}" for page in metadata["pages"]]
    default_page = len(page_options) - 1
    selected_label = st.selectbox("Pagina a firmar", options=page_options, index=default_page, key=f"page_{uploaded.file_id if hasattr(uploaded, 'file_id') else uploaded.name}")
    page_index = page_options.index(selected_label)
    page_data = metadata["pages"][page_index]

    default_width = min(180.0, page_data["width"] * 0.3)
    default_height = min(90.0, page_data["height"] * 0.12)
    default_x = max(20.0, page_data["width"] - default_width - 40.0)
    default_y_top = max(20.0, page_data["height"] - default_height - 80.0)

    c1, c2 = st.columns(2)
    with c1:
        width = st.number_input(
            "Ancho firma",
            min_value=60.0,
            max_value=float(page_data["width"]),
            value=float(round(default_width, 1)),
            step=5.0,
            key=f"sig_w_{uploaded.name}_{page_index}",
        )
        x_from_left = st.number_input(
            "Posicion X",
            min_value=0.0,
            max_value=max(0.0, float(page_data["width"] - width)),
            value=float(round(min(default_x, page_data["width"] - width), 1)),
            step=5.0,
            key=f"sig_x_{uploaded.name}_{page_index}",
        )
    with c2:
        height = st.number_input(
            "Alto firma",
            min_value=30.0,
            max_value=float(page_data["height"]),
            value=float(round(default_height, 1)),
            step=5.0,
            key=f"sig_h_{uploaded.name}_{page_index}",
        )
        y_from_top = st.number_input(
            "Posicion Y",
            min_value=0.0,
            max_value=max(0.0, float(page_data["height"] - height)),
            value=float(round(min(default_y_top, page_data["height"] - height), 1)),
            step=5.0,
            key=f"sig_y_{uploaded.name}_{page_index}",
        )

    preview_image = _build_preview_image(
        pdf_bytes=pdf_bytes,
        page_index=page_index,
        page_width=page_data["width"],
        page_height=page_data["height"],
        x=x_from_left,
        y_from_top=y_from_top,
        width=width,
        height=height,
    )
    if preview_image:
        st.image(preview_image, caption="Previsualizacion de la firma. Ajusta X/Y hasta verla bien.", use_container_width=True)
    else:
        st.info("No se pudo renderizar el PDF como imagen en este entorno. Puedes seguir ajustando la zona con X/Y.")

    pdf_y = float(page_data["height"] - y_from_top - height)
    return {
        "page_index": int(page_index),
        "x": float(x_from_left),
        "y": float(pdf_y),
        "width": float(width),
        "height": float(height),
    }


def _render_firmante_panel(profile: str) -> None:
    st.subheader("Panel Firmante")
    docs = get_documents_for_profile(profile)
    pending = [doc for doc in docs if doc["estado"] == "enviado"]

    top_left, top_right = st.columns([1.2, 1], gap="large")
    with top_left:
        st.markdown("### Pendientes por decidir")
        _render_documents_table(pending)
    with top_right:
        st.markdown("### Acciones")
        if not pending:
            st.info("No hay documentos pendientes.")
        else:
            options = {f"{doc['id']} - {doc['nombre_archivo']}": doc for doc in pending}
            selected_label = st.selectbox("Documento", options=list(options.keys()))
            selected_doc = options[selected_label]

            st.write(f"Estado actual: `{selected_doc['estado']}`")
            st.write(f"Ruta entrada: `{selected_doc['ruta_original']}`")
            if selected_doc.get("observaciones"):
                st.write(f"Observaciones: {selected_doc['observaciones']}")
            if selected_doc.get("firma_pagina") is not None:
                st.caption(
                    "Zona lista: "
                    f"pagina {int(selected_doc['firma_pagina']) + 1}, "
                    f"x={round(float(selected_doc['firma_x'] or 0), 1)}, "
                    f"y={round(float(selected_doc['firma_y'] or 0), 1)}"
                )

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Firmar", type="primary", use_container_width=True):
                    try:
                        output_path = sign_document(selected_doc["id"], get_profile_meta(profile)["nombre"])
                        st.success(f"Documento firmado y cargado a salida: {output_path}")
                    except Exception as exc:
                        st.error(str(exc))
            with c2:
                reject_reason = st.text_input("Motivo rechazo", key=f"reject_reason_{selected_doc['id']}")
                if st.button("Rechazar", use_container_width=True):
                    try:
                        reject_document(selected_doc["id"], get_profile_meta(profile)["nombre"], reject_reason)
                        st.warning("Documento rechazado y registrado.")
                    except Exception as exc:
                        st.error(str(exc))

    st.markdown("### Documentos ya procesados")
    processed = [doc for doc in get_all_documents() if doc["estado"] in {"firmado", "rechazado"}]
    _render_documents_table(processed)
    _render_download_section(processed, title="Descargar salida")


def _render_history() -> None:
    st.subheader("Historial")
    history = get_history(100)
    if not history:
        st.info("Aun no hay movimientos registrados.")
        return
    st.dataframe(
        [
            {
                "Fecha": item["fecha"],
                "Documento": item.get("nombre_archivo", ""),
                "Accion": item["accion"],
                "Usuario": item["usuario"],
                "Detalle": item.get("detalles", ""),
            }
            for item in history
        ],
        use_container_width=True,
        hide_index=True,
    )


def _render_settings() -> None:
    st.subheader("Configuracion")
    settings = get_settings()
    with st.form("settings_form"):
        st.markdown("### Almacenamiento")
        storage_mode = st.selectbox("Modo storage", ["local", "onedrive_api"], index=["local", "onedrive_api"].index(settings.get("storage_mode", "local") or "local"))
        local_base_dir = st.text_input("Base local", value=settings.get("storage_local_base_dir", ""))
        local_inbox_dir = st.text_input("Carpeta entrada", value=settings.get("storage_local_inbox_dir", ""))
        local_signed_dir = st.text_input("Carpeta firmados", value=settings.get("storage_local_signed_dir", ""))
        local_rejected_dir = st.text_input("Carpeta rechazados", value=settings.get("storage_local_rejected_dir", ""))
        local_temp_dir = st.text_input("Carpeta temporal", value=settings.get("storage_local_temp_dir", ""))

        st.markdown("### Registro")
        registry_mode = st.selectbox("Modo registro", ["csv", "excel_online", "google_sheets", "disabled"], index=["csv", "excel_online", "google_sheets", "disabled"].index(settings.get("registry_mode", "csv") or "csv"))
        registry_csv_path = st.text_input("Ruta CSV", value=settings.get("registry_csv_path", ""))

        st.markdown("### Firma")
        firma_path = st.text_input("Imagen firma", value=settings.get("firma_path", ""))
        pfx_path = st.text_input("Certificado PFX", value=settings.get("pfx_path", ""))
        pfx_pass = st.text_input("Password PFX", value=settings.get("pfx_pass", ""), type="password")

        st.markdown("### OneDrive API")
        onedrive_tenant_id = st.text_input("Tenant ID", value=settings.get("onedrive_tenant_id", ""))
        onedrive_client_id = st.text_input("Client ID", value=settings.get("onedrive_client_id", ""))
        onedrive_client_secret = st.text_input("Client Secret", value=settings.get("onedrive_client_secret", ""), type="password")
        onedrive_drive_id = st.text_input("Drive ID", value=settings.get("onedrive_drive_id", ""))
        onedrive_folder_inbox = st.text_input("Folder entrada", value=settings.get("onedrive_folder_inbox", ""))
        onedrive_folder_signed = st.text_input("Folder firmados", value=settings.get("onedrive_folder_signed", ""))
        onedrive_folder_rejected = st.text_input("Folder rechazados", value=settings.get("onedrive_folder_rejected", ""))

        saved = st.form_submit_button("Guardar configuracion", use_container_width=True)
        if saved:
            update_settings(
                {
                    "storage_mode": storage_mode,
                    "storage_local_base_dir": local_base_dir,
                    "storage_local_inbox_dir": local_inbox_dir,
                    "storage_local_signed_dir": local_signed_dir,
                    "storage_local_rejected_dir": local_rejected_dir,
                    "storage_local_temp_dir": local_temp_dir,
                    "registry_mode": registry_mode,
                    "registry_csv_path": registry_csv_path,
                    "firma_path": firma_path,
                    "pfx_path": pfx_path,
                    "pfx_pass": pfx_pass,
                    "onedrive_tenant_id": onedrive_tenant_id,
                    "onedrive_client_id": onedrive_client_id,
                    "onedrive_client_secret": onedrive_client_secret,
                    "onedrive_drive_id": onedrive_drive_id,
                    "onedrive_folder_inbox": onedrive_folder_inbox,
                    "onedrive_folder_signed": onedrive_folder_signed,
                    "onedrive_folder_rejected": onedrive_folder_rejected,
                }
            )
            st.success("Configuracion guardada.")


def _render_documents_table(documents: List[Dict]) -> None:
    if not documents:
        st.info("No hay documentos para mostrar.")
        return
    st.dataframe(
        [
            {
                "ID": doc["id"],
                "Archivo": doc["nombre_archivo"],
                "Estado": doc["estado"],
                "Remitente": doc.get("remitente", ""),
                "Destinatario": doc.get("destinatario", ""),
                "Fecha envio": doc.get("fecha_envio", ""),
                "Fecha firma": doc.get("fecha_firma", ""),
                "Zona firma": _format_signature_zone(doc),
                "Observaciones": doc.get("observaciones", ""),
            }
            for doc in documents
        ],
        use_container_width=True,
        hide_index=True,
    )


def _render_download_section(documents: List[Dict], title: str) -> None:
    if not documents:
        return
    st.markdown(f"### {title}")
    available = {
        f"{doc['id']} - {doc['nombre_archivo']} ({doc['estado']})": doc
        for doc in documents
        if doc.get("ruta_backup") or doc.get("ruta_original")
    }
    if not available:
        st.caption("No hay archivos disponibles para descargar todavia.")
        return

    selected_label = st.selectbox(title, options=list(available.keys()), key=f"download_{title}")
    selected_doc = available[selected_label]
    file_path = selected_doc.get("ruta_backup") or selected_doc.get("ruta_original")

    backend = get_storage_backend()
    try:
        file_bytes = backend.read_bytes(file_path)
        st.download_button(
            "Descargar PDF",
            data=file_bytes,
            file_name=os.path.basename(file_path),
            mime="application/pdf",
            use_container_width=True,
            key=f"download_button_{selected_doc['id']}_{title}",
        )
    except Exception as exc:
        st.caption(f"No se pudo leer el archivo desde el backend actual: {exc}")


def _get_pdf_metadata(pdf_bytes: bytes) -> Dict:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for index, page in enumerate(reader.pages):
        pages.append(
            {
                "index": index,
                "width": float(page.mediabox.width),
                "height": float(page.mediabox.height),
            }
        )
    return {"pages": pages}


def _build_preview_image(
    *,
    pdf_bytes: bytes,
    page_index: int,
    page_width: float,
    page_height: float,
    x: float,
    y_from_top: float,
    width: float,
    height: float,
) -> Optional[Image.Image]:
    image = _render_pdf_page(pdf_bytes, page_index)
    if image is None:
        return None

    preview = image.copy()
    draw = ImageDraw.Draw(preview, "RGBA")
    scale_x = preview.width / float(page_width)
    scale_y = preview.height / float(page_height)
    left = x * scale_x
    top = y_from_top * scale_y
    right = left + width * scale_x
    bottom = top + height * scale_y
    draw.rectangle((left, top, right, bottom), outline=(220, 30, 30, 255), width=4, fill=(220, 30, 30, 70))
    return preview


def _render_pdf_page(pdf_bytes: bytes, page_index: int) -> Optional[Image.Image]:
    if fitz is None:
        return None
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = document.load_page(page_index)
    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    return Image.open(io.BytesIO(pixmap.tobytes("png")))


def _format_signature_zone(doc: Dict) -> str:
    if doc.get("firma_pagina") is None:
        return ""
    return f"P{int(doc['firma_pagina']) + 1} ({round(float(doc.get('firma_x') or 0), 0)}, {round(float(doc.get('firma_y') or 0), 0)})"


if __name__ == "__main__":
    run()
