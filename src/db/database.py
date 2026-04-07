import os
import sqlite3
from pathlib import Path

# Configuración de base de datos
APP_DIR = Path("C:/Gestion_Firmas")
DB_APP = APP_DIR / "sdgf.db"

def get_db_connection():
    """Obtiene una conexión a la base de datos (con soporte de columnas por nombre)."""
    os.makedirs(APP_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_APP)
    conn.row_factory = sqlite3.Row  # Para acceder como diccionarios
    return conn

def init_db():
    """Crea las tablas iniciales si no existen."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Tabla Documentos principal
    c.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_archivo TEXT NOT NULL,
            ruta_original TEXT NOT NULL,
            ruta_backup TEXT,
            remitente TEXT,
            destinatario TEXT,
            estado TEXT NOT NULL DEFAULT 'enviado',
            categoria TEXT,
            rol_origen TEXT NOT NULL DEFAULT 'emisor',
            fecha_envio TEXT,
            fecha_recibo TEXT,
            fecha_firma TEXT,
            observaciones TEXT
        )
    ''')
    
    # Tabla Historial para auditoría
    c.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            documento_id INTEGER NOT NULL,
            accion TEXT NOT NULL,
            usuario TEXT NOT NULL,
            fecha TEXT NOT NULL,
            detalles TEXT,
            FOREIGN KEY(documento_id) REFERENCES documentos(id)
        )
    ''')
    
    # Tabla Configuración Rutas
    c.execute('''
        CREATE TABLE IF NOT EXISTS config_rutas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_documento TEXT NOT NULL UNIQUE,
            correo_destino TEXT NOT NULL
        )
    ''')
    
    # Tabla Settings
    c.execute('''
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    ''')

    _ensure_column(c, "documentos", "firma_pagina", "INTEGER")
    _ensure_column(c, "documentos", "firma_x", "REAL")
    _ensure_column(c, "documentos", "firma_y", "REAL")
    _ensure_column(c, "documentos", "firma_w", "REAL")
    _ensure_column(c, "documentos", "firma_h", "REAL")
    
    conn.commit()
    conn.close()


def _ensure_column(cursor, table_name, column_name, column_type):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {row[1] for row in cursor.fetchall()}
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
