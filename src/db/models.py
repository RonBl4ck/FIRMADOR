from src.db.database import get_db_connection
import datetime

class DocumentoService:
    @staticmethod
    def get_all(rol="emisor"):
        """
        Emisor (Secretaria) ve los docs que ELLA envió → rol_origen='emisor'
        Firmante (Jefe) ve los docs que le LLEGARON → rol_origen='emisor' (los mismos, pero desde su perspectiva)
        Ambos ven la misma data pero con acciones diferentes en la UI.
        """
        conn = get_db_connection()
        c = conn.cursor()
        
        if rol == "emisor":
            # La Secretaria ve lo que ella ha enviado, ordenado por más reciente
            c.execute("SELECT * FROM documentos WHERE rol_origen = 'emisor' ORDER BY id DESC")
        else:
            # El Jefe ve lo que le han enviado para firmar
            c.execute("SELECT * FROM documentos WHERE rol_origen = 'emisor' OR rol_origen = 'firmante_import' ORDER BY id DESC")
            
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_by_id(doc_id):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM documentos WHERE id = ?", (doc_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def agregar_documento(nombre, ruta_original, remitente=None, destinatario=None, estado="enviado", categoria=None, rol_origen="emisor", fecha_envio=None, fecha_recibo=None):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO documentos (nombre_archivo, ruta_original, remitente, destinatario, estado, categoria, rol_origen, fecha_envio, fecha_recibo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, ruta_original, remitente, destinatario, estado, categoria, rol_origen, fecha_envio, fecha_recibo))
        doc_id = c.lastrowid
        conn.commit()
        conn.close()
        
        # Guardar en historial
        HistorialService.log(doc_id, "Documento Ingresado", remitente or destinatario or "Sistema")
        return doc_id

    @staticmethod
    def actualizar_estado(doc_id, nuevo_estado, ruta_backup=None):
        conn = get_db_connection()
        c = conn.cursor()
        
        if ruta_backup:
            c.execute("UPDATE documentos SET estado = ?, ruta_backup = ?, fecha_firma = ? WHERE id = ?", 
                     (nuevo_estado, ruta_backup, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), doc_id))
        else:
            c.execute("UPDATE documentos SET estado = ? WHERE id = ?", (nuevo_estado, doc_id))
            
        conn.commit()
        conn.close()
    
    @staticmethod
    def existe_archivo(nombre_archivo):
        """Verifica si un archivo ya fue registrado (evita duplicados del Watcher)."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM documentos WHERE nombre_archivo = ?", (nombre_archivo,))
        count = c.fetchone()["cnt"]
        conn.close()
        return count > 0

class HistorialService:
    @staticmethod
    def log(doc_id, accion, usuario, detalles=""):
        conn = get_db_connection()
        c = conn.cursor()
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            INSERT INTO historial (documento_id, accion, usuario, fecha, detalles)
            VALUES (?, ?, ?, ?, ?)
        """, (doc_id, accion, usuario, fecha, detalles))
        conn.commit()
        conn.close()
        
    @staticmethod
    def get_recent(limit=50):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT h.*, d.nombre_archivo, d.ruta_backup, d.ruta_original
            FROM historial h
            LEFT JOIN documentos d ON h.documento_id = d.id
            ORDER BY h.id DESC LIMIT ?
        """, (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

class ConfigService:
    @staticmethod
    def get(clave, default=None):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
        row = c.fetchone()
        conn.close()
        return row["valor"] if row else default
        
    @staticmethod
    def set(clave, valor):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", (clave, str(valor)))
        conn.commit()
        conn.close()
