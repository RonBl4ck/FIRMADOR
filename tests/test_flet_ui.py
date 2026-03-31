"""
=============================================================================
SDGF - Test 3: Prototipo de Interfaz en Flet
=============================================================================
Valida que Flet funciona correctamente con:
  1. Navegación por pestañas (Emisor, Firmante, Historial, Configuración)
  2. Tablas con bolitas de estado (4 colores)
  3. Botones interactivos
  4. Tema oscuro premium
=============================================================================
"""

import flet as ft
import datetime
import json
import os

# ============================================================================
# DATOS MOCK
# ============================================================================
MOCK_EMISOR_DATA = [
    {"archivo": "Contrato_Servicios_2026.pdf", "fecha_envio": "2026-03-14 09:30", "destinatario": "jefe.garcia@empresa.com", "estado": "enviado"},
    {"archivo": "Acta_Reunion_Marzo.pdf", "fecha_envio": "2026-03-15 11:15", "destinatario": "director.lopez@empresa.com", "estado": "firmado"},
    {"archivo": "Presupuesto_Q1.pdf", "fecha_envio": "2026-03-16 08:00", "destinatario": "gerente.ruiz@empresa.com", "estado": "finalizado"},
    {"archivo": "Informe_Auditoria.pdf", "fecha_envio": "2026-03-10 14:45", "destinatario": "jefe.garcia@empresa.com", "estado": "rechazado"},
    {"archivo": "Orden_Compra_4521.pdf", "fecha_envio": "2026-03-12 16:20", "destinatario": "director.lopez@empresa.com", "estado": "enviado"},
]

MOCK_FIRMANTE_DATA = [
    {"archivo": "Contrato_Servicios_2026.pdf", "fecha_recibo": "2026-03-14 09:32", "remitente": "asistente.perez@empresa.com", "estado": "enviado"},
    {"archivo": "Memo_Interno_045.pdf", "fecha_recibo": "2026-03-15 10:00", "remitente": "coordinador.diaz@empresa.com", "estado": "firmado"},
    {"archivo": "Solicitud_Vacaciones_RH.pdf", "fecha_recibo": "2026-03-13 08:45", "remitente": "rrhh@empresa.com", "estado": "finalizado"},
    {"archivo": "Presupuesto_Depto_TI.pdf", "fecha_recibo": "2026-03-11 13:20", "remitente": "ti.soporte@empresa.com", "estado": "rechazado"},
]

MOCK_HISTORIAL = [
    {"archivo": "Contrato_2025_firmado.pdf", "accion": "Firmado y enviado", "usuario": "Gerente García", "fecha": "2026-03-10 09:30", "ruta": "C:/Gestion_Firmas/Backup/Contrato_2025_firmado.pdf"},
    {"archivo": "Acta_Feb_firmado.pdf", "accion": "Firmado y enviado", "usuario": "Director López", "fecha": "2026-03-08 14:15", "ruta": "C:/Gestion_Firmas/Backup/Acta_Feb_firmado.pdf"},
    {"archivo": "Orden_4500.pdf", "accion": "Enviado para firma", "usuario": "Asistente Pérez", "fecha": "2026-03-07 11:00", "ruta": "C:/Gestion_Firmas/Backup/Orden_4500.pdf"},
    {"archivo": "Informe_Ene.pdf", "accion": "Rechazado", "usuario": "Gerente García", "fecha": "2026-03-05 16:45", "ruta": "C:/Gestion_Firmas/Backup/Informe_Ene.pdf"},
    {"archivo": "Memo_032_firmado.pdf", "accion": "Firmado y enviado", "usuario": "Director López", "fecha": "2026-03-03 10:20", "ruta": "C:/Gestion_Firmas/Backup/Memo_032_firmado.pdf"},
]

# ============================================================================
# CONSTANTES DE DISEÑO
# ============================================================================
COLORS = {
    "bg_dark": "#0f0f1a",
    "bg_card": "#1a1a2e",
    "bg_card_hover": "#222240",
    "accent_purple": "#7c3aed",
    "accent_blue": "#3b82f6",
    "accent_gradient_start": "#6366f1",
    "accent_gradient_end": "#8b5cf6",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "border": "#2d2d4a",
    "status_red": "#ef4444",
    "status_yellow": "#eab308",
    "status_green": "#22c55e",
    "status_blue": "#3b82f6",
    "danger": "#dc2626",
}

STATUS_CONFIG = {
    "enviado":     {"color": COLORS["status_red"],    "label": "En Bandeja",  "icon": ft.Icons.CIRCLE,         "emoji": "🔴"},
    "firmado":     {"color": COLORS["status_yellow"], "label": "En Revisión", "icon": ft.Icons.CIRCLE,         "emoji": "🟡"},
    "finalizado":  {"color": COLORS["status_green"],  "label": "Finalizado",  "icon": ft.Icons.CHECK_CIRCLE,   "emoji": "🟢"},
    "rechazado":   {"color": COLORS["status_blue"],   "label": "Rechazado",   "icon": ft.Icons.CANCEL,         "emoji": "🔵"},
}


# ============================================================================
# COMPONENTES UI
# ============================================================================

def create_status_badge(estado: str) -> ft.Container:
    """Crea una bolita de estado con color y tooltip."""
    config = STATUS_CONFIG.get(estado, STATUS_CONFIG["enviado"])
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(config["icon"], color=config["color"], size=16),
                ft.Text(config["label"], color=config["color"], size=12, weight=ft.FontWeight.W_600),
            ],
            spacing=6,
        ),
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        border_radius=20,
        bgcolor=f"{config['color']}15",
        border=ft.Border.all(1, f"{config['color']}40"),
        tooltip=f"Estado: {config['label']}",
    )


def create_status_legend() -> ft.Container:
    """Crea la leyenda de estados."""
    items = []
    for key, config in STATUS_CONFIG.items():
        items.append(
            ft.Row(
                [
                    ft.Icon(ft.Icons.CIRCLE, color=config["color"], size=10),
                    ft.Text(config["label"], color=COLORS["text_secondary"], size=11),
                ],
                spacing=4,
            )
        )
    return ft.Container(
        content=ft.Row(items, spacing=16),
        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
        border_radius=8,
        bgcolor=COLORS["bg_card"],
        border=ft.Border.all(1, COLORS["border"]),
    )


def create_header(page: ft.Page) -> ft.Container:
    """Crea el header de la app."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(ft.Icons.DRAW, color="#ffffff", size=24),
                            width=44,
                            height=44,
                            border_radius=12,
                            gradient=ft.LinearGradient(
                                begin=ft.Alignment.TOP_LEFT,
                                end=ft.Alignment.BOTTOM_RIGHT,
                                colors=[COLORS["accent_gradient_start"], COLORS["accent_gradient_end"]],
                            ),
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.Text("SDGF", size=20, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                                ft.Text("Sistema Dual de Gestión de Firmas", size=11, color=COLORS["text_secondary"]),
                            ],
                            spacing=0,
                        ),
                    ],
                    spacing=12,
                ),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.CIRCLE, color=COLORS["status_green"], size=8),
                                    ft.Text("Outlook Conectado", size=11, color=COLORS["text_secondary"]),
                                ],
                                spacing=6,
                            ),
                            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                            border_radius=20,
                            bgcolor=f"{COLORS['status_green']}10",
                            border=ft.Border.all(1, f"{COLORS['status_green']}30"),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.NOTIFICATIONS_OUTLINED,
                            icon_color=COLORS["text_secondary"],
                            icon_size=20,
                            tooltip="Notificaciones",
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS_OUTLINED,
                            icon_color=COLORS["text_secondary"],
                            icon_size=20,
                            tooltip="Configuración",
                        ),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding.symmetric(horizontal=24, vertical=16),
        bgcolor=COLORS["bg_card"],
        border=ft.Border.only(bottom=ft.BorderSide(1, COLORS["border"])),
    )


def create_stats_cards() -> ft.Row:
    """Crea las tarjetas de estadísticas."""
    stats = [
        {"label": "En Bandeja", "value": "3", "icon": ft.Icons.INBOX, "color": COLORS["status_red"], "change": "+2 hoy"},
        {"label": "En Revisión", "value": "2", "icon": ft.Icons.RATE_REVIEW, "color": COLORS["status_yellow"], "change": "1 pendiente"},
        {"label": "Finalizados", "value": "12", "icon": ft.Icons.CHECK_CIRCLE, "color": COLORS["status_green"], "change": "+5 esta semana"},
        {"label": "Rechazados", "value": "1", "icon": ft.Icons.CANCEL, "color": COLORS["status_blue"], "change": "0 hoy"},
    ]
    
    cards = []
    for stat in stats:
        cards.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(stat["icon"], color=stat["color"], size=20),
                                    width=36,
                                    height=36,
                                    border_radius=8,
                                    bgcolor=f"{stat['color']}15",
                                    alignment=ft.Alignment.CENTER,
                                ),
                                ft.Text(stat["label"], color=COLORS["text_secondary"], size=12),
                            ],
                            spacing=10,
                        ),
                        ft.Text(stat["value"], size=32, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                        ft.Text(stat["change"], size=11, color=COLORS["text_muted"]),
                    ],
                    spacing=8,
                ),
                padding=20,
                border_radius=12,
                bgcolor=COLORS["bg_card"],
                border=ft.Border.all(1, COLORS["border"]),
                expand=True,
                animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
            )
        )
    
    return ft.Row(cards, spacing=16)


def is_overdue(fecha_str: str) -> bool:
    """Verifica si un documento lleva más de 24h."""
    try:
        fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d %H:%M")
        return (datetime.datetime.now() - fecha).total_seconds() > 86400
    except ValueError:
        return False


def create_document_table(data: list, columns: list, page: ft.Page, role: str) -> ft.Container:
    """Crea una tabla de documentos con estilo premium."""
    
    selected_rows = set()
    
    # Build header
    header_cells = []
    for col in columns:
        header_cells.append(
            ft.Container(
                content=ft.Text(col["label"], size=11, weight=ft.FontWeight.W_600, color=COLORS["text_muted"]),
                expand=col.get("expand", True),
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            )
        )
    
    header = ft.Container(
        content=ft.Row(header_cells, spacing=0),
        bgcolor=COLORS["bg_dark"],
        border_radius=ft.BorderRadius.only(top_left=8, top_right=8),
        border=ft.Border.all(1, COLORS["border"]),
    )
    
    # Build rows
    rows = []
    for idx, item in enumerate(data):
        overdue = is_overdue(item.get("fecha_envio", item.get("fecha_recibo", "")))
        row_bgcolor = "#2a1a1a" if (overdue and item["estado"] == "enviado") else COLORS["bg_card"]
        
        cells = []
        for col in columns:
            key = col["key"]
            if key == "estado":
                cell_content = create_status_badge(item[key])
            elif key == "archivo":
                name_parts = []
                name_parts.append(ft.Icon(ft.Icons.PICTURE_AS_PDF, color="#ef4444", size=16))
                name_parts.append(ft.Text(item[key], size=13, color=COLORS["text_primary"], weight=ft.FontWeight.W_500))
                if overdue and item["estado"] == "enviado":
                    name_parts.append(
                        ft.Container(
                            content=ft.Text("⏰ >24h", size=9, color=COLORS["status_red"], weight=ft.FontWeight.BOLD),
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            border_radius=4,
                            bgcolor=f"{COLORS['status_red']}20",
                        )
                    )
                cell_content = ft.Row(name_parts, spacing=8)
            else:
                cell_content = ft.Text(item.get(key, ""), size=13, color=COLORS["text_secondary"])
            
            cells.append(
                ft.Container(
                    content=cell_content,
                    expand=col.get("expand", True),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=12),
                )
            )
        
        row = ft.Container(
            content=ft.Row(cells, spacing=0),
            bgcolor=row_bgcolor,
            border=ft.Border.only(
                left=ft.BorderSide(1, COLORS["border"]),
                right=ft.BorderSide(1, COLORS["border"]),
                bottom=ft.BorderSide(1, COLORS["border"]),
            ),
            on_hover=lambda e, bg=row_bgcolor: _handle_row_hover(e, bg),
            animate=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
        )
        rows.append(row)
    
    # Action buttons
    if role == "emisor":
        action_btn = ft.ElevatedButton(
            content="Subir y Enviar",
            icon=ft.Icons.UPLOAD_FILE,
            bgcolor=COLORS["accent_purple"],
            color="#ffffff",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=24, vertical=12),
            ),
            on_click=lambda e: _show_snackbar(page, "📤 Función de envío - Se activará en la versión final"),
        )
    else:
        action_btn = ft.ElevatedButton(
            content="Firmar y Devolver",
            icon=ft.Icons.DRAW,
            bgcolor=COLORS["status_green"],
            color="#ffffff",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.symmetric(horizontal=24, vertical=12),
            ),
            on_click=lambda e: _show_snackbar(page, "✍️ Función de firma - Se activará en la versión final"),
            disabled=True,  # Se habilita al seleccionar archivo
            tooltip="Selecciona un archivo primero",
        )
    
    action_bar = ft.Container(
        content=ft.Row(
            [
                ft.Text(f"{len(data)} documento(s)", color=COLORS["text_muted"], size=12),
                ft.Row(
                    [
                        ft.OutlinedButton(
                            content="Actualizar",
                            icon=ft.Icons.REFRESH,
                            style=ft.ButtonStyle(
                                color=COLORS["text_secondary"],
                                side=ft.BorderSide(1, COLORS["border"]),
                                shape=ft.RoundedRectangleBorder(radius=8),
                                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                            ),
                            on_click=lambda e: _show_snackbar(page, "🔄 Lista actualizada"),
                        ),
                        action_btn,
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
    )
    
    return ft.Container(
        content=ft.Column(
            [header] + rows + [action_bar],
            spacing=0,
        ),
        border_radius=12,
        bgcolor=COLORS["bg_card"],
        border=ft.Border.all(1, COLORS["border"]),
    )


def _handle_row_hover(e, default_bg):
    """Maneja el hover sobre las filas de la tabla."""
    if e.data == "true":
        e.control.bgcolor = COLORS["bg_card_hover"]
    else:
        e.control.bgcolor = default_bg
    e.control.update()


def _show_snackbar(page, message):
    """Muestra un snackbar con mensaje."""
    page.open(
        ft.SnackBar(
            content=ft.Text(message, color="#ffffff"),
            bgcolor=COLORS["accent_purple"],
            duration=3000,
        )
    )


# ============================================================================
# VISTAS (TABS)
# ============================================================================

def build_emisor_view(page: ft.Page) -> ft.Column:
    """Vista del perfil Emisor."""
    columns = [
        {"key": "archivo",       "label": "📄 Archivo",       "expand": True},
        {"key": "fecha_envio",   "label": "📅 Fecha Envío",   "expand": True},
        {"key": "destinatario",  "label": "👤 Destinatario",  "expand": True},
        {"key": "estado",        "label": "⚡ Estado",         "expand": True},
    ]
    
    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Panel del Emisor", size=22, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    create_status_legend(),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            create_stats_cards(),
            create_document_table(MOCK_EMISOR_DATA, columns, page, "emisor"),
        ],
        spacing=20,
    )


def build_firmante_view(page: ft.Page) -> ft.Column:
    """Vista del perfil Firmante."""
    columns = [
        {"key": "archivo",       "label": "📄 Archivo",        "expand": True},
        {"key": "fecha_recibo",  "label": "📅 Fecha Recibo",   "expand": True},
        {"key": "remitente",     "label": "👤 Remitente",      "expand": True},
        {"key": "estado",        "label": "⚡ Estado",          "expand": True},
    ]
    
    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Panel del Firmante", size=22, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    create_status_legend(),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            create_stats_cards(),
            create_document_table(MOCK_FIRMANTE_DATA, columns, page, "firmante"),
        ],
        spacing=20,
    )


def build_historial_view(page: ft.Page) -> ft.Column:
    """Vista de historial de acciones."""
    
    rows = []
    for item in MOCK_HISTORIAL:
        # Determine action icon and color
        if "Firmado" in item["accion"]:
            action_color = COLORS["status_green"]
            action_icon = ft.Icons.CHECK_CIRCLE
        elif "Rechazado" in item["accion"]:
            action_color = COLORS["status_blue"]
            action_icon = ft.Icons.CANCEL
        else:
            action_color = COLORS["status_yellow"]
            action_icon = ft.Icons.SEND
        
        row = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(action_icon, color=action_color, size=20),
                        width=40,
                        height=40,
                        border_radius=10,
                        bgcolor=f"{action_color}15",
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.PICTURE_AS_PDF, color="#ef4444", size=14),
                                    ft.Text(item["archivo"], size=14, weight=ft.FontWeight.W_500, color=COLORS["text_primary"]),
                                ],
                                spacing=6,
                            ),
                            ft.Text(f"{item['accion']} por {item['usuario']}", size=12, color=COLORS["text_secondary"]),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Column(
                        [
                            ft.Text(item["fecha"], size=12, color=COLORS["text_muted"]),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.FOLDER_OPEN,
                        icon_color=COLORS["accent_blue"],
                        icon_size=18,
                        tooltip=f"Abrir: {item['ruta']}",
                        on_click=lambda e, ruta=item["ruta"]: _show_snackbar(page, f"📂 Abriendo: {ruta}"),
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            bgcolor=COLORS["bg_card"],
            border=ft.Border.all(1, COLORS["border"]),
            border_radius=10,
            on_hover=lambda e: _handle_row_hover(e, COLORS["bg_card"]),
            animate=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
        )
        rows.append(row)
    
    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Historial de Actividad", size=22, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
                    ft.OutlinedButton(
                        content="Exportar Log",
                        icon=ft.Icons.DOWNLOAD,
                        style=ft.ButtonStyle(
                            color=COLORS["text_secondary"],
                            side=ft.BorderSide(1, COLORS["border"]),
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        on_click=lambda e: _show_snackbar(page, "📥 Exportación de log - Se activará en la versión final"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Container(
                content=ft.TextField(
                    hint_text="Buscar en historial...",
                    prefix_icon=ft.Icons.SEARCH,
                    border_color=COLORS["border"],
                    focused_border_color=COLORS["accent_purple"],
                    text_size=14,
                    hint_style=ft.TextStyle(color=COLORS["text_muted"]),
                    color=COLORS["text_primary"],
                    cursor_color=COLORS["accent_purple"],
                ),
            ),
            ft.Column(rows, spacing=8),
        ],
        spacing=16,
    )


def build_config_view(page: ft.Page) -> ft.Column:
    """Vista de configuración."""
    
    # Multi-destinatario mock routes
    routes_data = [
        {"tipo": "Contratos", "destinatario": "legal@empresa.com"},
        {"tipo": "Presupuestos", "destinatario": "finanzas@empresa.com"},
        {"tipo": "Actas", "destinatario": "secretaria@empresa.com"},
    ]
    
    route_rows = []
    for route in routes_data:
        route_rows.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(ft.Icons.ROUTE, color=COLORS["accent_purple"], size=18),
                            width=36,
                            height=36,
                            border_radius=8,
                            bgcolor=f"{COLORS['accent_purple']}15",
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.Text(route["tipo"], size=14, weight=ft.FontWeight.W_500, color=COLORS["text_primary"]),
                                ft.Text(route["destinatario"], size=12, color=COLORS["text_secondary"]),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color=COLORS["text_muted"],
                            icon_size=18,
                            tooltip="Editar ruta",
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=COLORS["danger"],
                            icon_size=18,
                            tooltip="Eliminar ruta",
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                bgcolor=COLORS["bg_card"],
                border=ft.Border.all(1, COLORS["border"]),
                border_radius=8,
            )
        )
    
    return ft.Column(
        [
            ft.Text("Configuración", size=22, weight=ft.FontWeight.BOLD, color=COLORS["text_primary"]),
            
            # Correo de retorno
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.EMAIL, color=COLORS["accent_purple"], size=20),
                                ft.Text("Correo de Retorno Predeterminado", size=16, weight=ft.FontWeight.W_600, color=COLORS["text_primary"]),
                            ],
                            spacing=8,
                        ),
                        ft.Text("Los documentos firmados se devolverán a esta dirección si no hay una ruta específica configurada.",
                                size=12, color=COLORS["text_secondary"]),
                        ft.TextField(
                            value="asistente.perez@empresa.com",
                            label="Correo de retorno",
                            prefix_icon=ft.Icons.ALTERNATE_EMAIL,
                            border_color=COLORS["border"],
                            focused_border_color=COLORS["accent_purple"],
                            text_size=14,
                            color=COLORS["text_primary"],
                            label_style=ft.TextStyle(color=COLORS["text_muted"]),
                            cursor_color=COLORS["accent_purple"],
                        ),
                    ],
                    spacing=12,
                ),
                padding=20,
                border_radius=12,
                bgcolor=COLORS["bg_card"],
                border=ft.Border.all(1, COLORS["border"]),
            ),
            
            # Firma
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.DRAW, color=COLORS["accent_purple"], size=20),
                                ft.Text("Imagen de Firma", size=16, weight=ft.FontWeight.W_600, color=COLORS["text_primary"]),
                            ],
                            spacing=8,
                        ),
                        ft.Text("Selecciona la imagen PNG de tu firma para estampar en los documentos.",
                                size=12, color=COLORS["text_secondary"]),
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, color=COLORS["text_muted"], size=40),
                                            ft.Text("Sin firma cargada", size=12, color=COLORS["text_muted"]),
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=8,
                                    ),
                                    width=200,
                                    height=100,
                                    border_radius=8,
                                    bgcolor=COLORS["bg_dark"],
                                    border=ft.Border.all(1, COLORS["border"]),
                                    alignment=ft.Alignment.CENTER,
                                ),
                                ft.ElevatedButton(
                                    content="Seleccionar Firma",
                                    icon=ft.Icons.UPLOAD,
                                    bgcolor=COLORS["accent_purple"],
                                    color="#ffffff",
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    ),
                                    on_click=lambda e: _show_snackbar(page, "🖼️ Selector de firma - Se activará en la versión final"),
                                ),
                            ],
                            spacing=16,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=12,
                ),
                padding=20,
                border_radius=12,
                bgcolor=COLORS["bg_card"],
                border=ft.Border.all(1, COLORS["border"]),
            ),
            
            # Rutas multi-destinatario
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.ROUTE, color=COLORS["accent_purple"], size=20),
                                ft.Text("Rutas de Destino", size=16, weight=ft.FontWeight.W_600, color=COLORS["text_primary"]),
                            ],
                            spacing=8,
                        ),
                        ft.Text("Configura rutas automáticas según el tipo de documento.",
                                size=12, color=COLORS["text_secondary"]),
                        ft.Column(route_rows, spacing=8),
                        ft.OutlinedButton(
                            content="Agregar Ruta",
                            icon=ft.Icons.ADD,
                            style=ft.ButtonStyle(
                                color=COLORS["accent_purple"],
                                side=ft.BorderSide(1, COLORS["accent_purple"]),
                                shape=ft.RoundedRectangleBorder(radius=8),
                            ),
                            on_click=lambda e: _show_snackbar(page, "➕ Agregar ruta - Se activará en la versión final"),
                        ),
                    ],
                    spacing=12,
                ),
                padding=20,
                border_radius=12,
                bgcolor=COLORS["bg_card"],
                border=ft.Border.all(1, COLORS["border"]),
            ),
            
            # Backup
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.BACKUP, color=COLORS["accent_purple"], size=20),
                                ft.Text("Respaldo Local", size=16, weight=ft.FontWeight.W_600, color=COLORS["text_primary"]),
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            [
                                ft.Text("Carpeta de backup:", size=13, color=COLORS["text_secondary"]),
                                ft.Container(
                                    content=ft.Text("C:/Gestion_Firmas/Backup", size=13, color=COLORS["accent_blue"]),
                                    padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                    border_radius=6,
                                    bgcolor=f"{COLORS['accent_blue']}10",
                                ),
                            ],
                            spacing=8,
                        ),
                    ],
                    spacing=8,
                ),
                padding=20,
                border_radius=12,
                bgcolor=COLORS["bg_card"],
                border=ft.Border.all(1, COLORS["border"]),
            ),
            
            # Save button
            ft.Row(
                [
                    ft.ElevatedButton(
                        content="Guardar Configuración",
                        icon=ft.Icons.SAVE,
                        bgcolor=COLORS["status_green"],
                        color="#ffffff",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.Padding.symmetric(horizontal=24, vertical=14),
                        ),
                        on_click=lambda e: _show_snackbar(page, "💾 Configuración guardada exitosamente"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.END,
            ),
        ],
        spacing=20,
        scroll=ft.ScrollMode.AUTO,
    )


# ============================================================================
# APP PRINCIPAL
# ============================================================================

def main(page: ft.Page):
    try:
        _main_impl(page)
    except Exception as e:
        import traceback
        with open("tests/crash_log.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        raise e

def _main_impl(page: ft.Page):
    # Window config
    page.title = "SDGF - Sistema Dual de Gestión de Firmas"
    page.bgcolor = COLORS["bg_dark"]
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 900
    page.window.min_height = 600
    page.padding = 0
    page.spacing = 0
    page.fonts = {
        "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    }
    page.theme = ft.Theme(font_family="Inter")
    
    # Content area (will switch based on selected tab)
    content_area = ft.Container(expand=True)
    
    def switch_tab(tab_name):
        """Cambia el contenido según la pestaña seleccionada."""
        if tab_name == "emisor":
            content_area.content = build_emisor_view(page)
        elif tab_name == "firmante":
            content_area.content = build_firmante_view(page)
        elif tab_name == "historial":
            content_area.content = build_historial_view(page)
        elif tab_name == "config":
            content_area.content = build_config_view(page)
        content_area.update()
        
        # Update nav button styles
        for btn_name, btn in nav_buttons.items():
            if btn_name == tab_name:
                btn.style = ft.ButtonStyle(
                    bgcolor=f"{COLORS['accent_purple']}20",
                    color=COLORS["accent_purple"],
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                    side=ft.BorderSide(1, COLORS["accent_purple"]),
                )
            else:
                btn.style = ft.ButtonStyle(
                    bgcolor="transparent",
                    color=COLORS["text_secondary"],
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.Padding.symmetric(horizontal=20, vertical=12),
                )
            btn.update()
    
    # Navigation buttons
    nav_buttons = {
        "emisor": ft.TextButton(
            content="Emisor",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=lambda e: switch_tab("emisor"),
        ),
        "firmante": ft.TextButton(
            content="Firmante",
            icon=ft.Icons.DRAW,
            on_click=lambda e: switch_tab("firmante"),
        ),
        "historial": ft.TextButton(
            content="Historial",
            icon=ft.Icons.HISTORY,
            on_click=lambda e: switch_tab("historial"),
        ),
        "config": ft.TextButton(
            content="Configuración",
            icon=ft.Icons.SETTINGS,
            on_click=lambda e: switch_tab("config"),
        ),
    }
    
    nav_bar = ft.Container(
        content=ft.Row(
            list(nav_buttons.values()),
            spacing=8,
        ),
        padding=ft.Padding.symmetric(horizontal=24, vertical=8),
        bgcolor=COLORS["bg_dark"],
    )
    
    # Scrollable content wrapper
    scrollable_content = ft.Container(
        content=content_area,
        padding=ft.Padding.symmetric(horizontal=24, vertical=16),
        expand=True,
    )
    
    # Main layout
    page.add(
        ft.Column(
            [
                create_header(page),
                nav_bar,
                ft.Container(
                    content=ft.Column(
                        [scrollable_content],
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )
    )
    
    # Initialize with Emisor view
    switch_tab("emisor")


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER)
