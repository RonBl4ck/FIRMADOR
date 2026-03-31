import os
import time
import shutil
from pathlib import Path
import threading
from src.db.models import DocumentoService, ConfigService

# Estado global
_watcher_running = False
_watcher_thread = None

# Rutas por defecto (se sobreescriben desde Config/DB)
DEFAULT_BASE = "C:/Gestion_Firmas/FIRMAPDF"
DEFAULT_INPUT = f"{DEFAULT_BASE}/INPUT"
DEFAULT_OUTPUT = f"{DEFAULT_BASE}/OUTPUT"

def _get_path(key, default):
    custom = ConfigService.get(key, None)
    if custom and os.path.isdir(custom):
        return Path(custom)
    return Path(default)

def get_input_dir():
    return _get_path("ruta_input", DEFAULT_INPUT)

def get_output_dir():
    return _get_path("ruta_output", DEFAULT_OUTPUT)

def _process_input_file(filepath):
    """Firmante: detecta un nuevo PDF en INPUT (enviado por el Emisor)."""
    filename = os.path.basename(filepath)
    
    if DocumentoService.existe_archivo(filename):
        return False
    
    # Verificar que el archivo no se esté escribiendo aún
    try:
        size1 = os.path.getsize(filepath)
        time.sleep(1)
        size2 = os.path.getsize(filepath)
        if size1 != size2:
            return False  # Aún se está copiando/sincronizando
    except OSError:
        return False
    
    import datetime
    fecha_ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    DocumentoService.agregar_documento(
        nombre=filename,
        ruta_original=str(filepath),
        remitente="Flujo Emisor",
        destinatario="Flujo Firmante",
        estado="enviado",
        categoria="Auto-detectado",
        rol_origen="emisor",
        fecha_recibo=fecha_ahora,
        fecha_envio=fecha_ahora
    )
    
    print(f"[Watcher-INPUT] Nuevo doc: {filename}")
    
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast("SDGF: Nuevo Documento", f"Recibido: {filename}", duration=3, threaded=True)
    except Exception:
        pass
    
    return True

def _process_output_file(filepath):
    """Emisor: detecta un PDF firmado/rechazado en OUTPUT (devuelto por el Jefe)."""
    filename = os.path.basename(filepath)
    
    # Buscar el doc original en la DB por nombre base (sin _firmado)
    nombre_base = filename.replace("_firmado", "")
    
    # Intentar encontrar el doc original
    from src.db.models import HistorialService
    import datetime
    
    docs = DocumentoService.get_all("emisor")
    found = False
    for d in docs:
        if d["nombre_archivo"] in filename or filename in d["nombre_archivo"] or d["nombre_archivo"].replace(".pdf", "") in filename:
            if d["estado"] != "finalizado":
                DocumentoService.actualizar_estado(d["id"], "finalizado", str(filepath))
                HistorialService.log(d["id"], "Documento firmado recibido de vuelta", "Sistema")
                found = True
                break
    
    if not found and not DocumentoService.existe_archivo(filename):
        # Registrar como nuevo doc devuelto
        fecha_ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        DocumentoService.agregar_documento(
            nombre=filename,
            ruta_original=str(filepath),
            remitente="Flujo Firmante",
            destinatario="Flujo Emisor",
            estado="finalizado",
            categoria="Devuelto firmado",
            rol_origen="firmante_devuelto",
            fecha_recibo=fecha_ahora
        )
    
    print(f"[Watcher-OUTPUT] Doc devuelto: {filename}")
    
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast("SDGF: Documento Devuelto", f"Firmado: {filename}", duration=3, threaded=True)
    except Exception:
        pass
    
    return True

def _watcher_loop(callback_on_change):
    """Vigila ambas carpetas INPUT y OUTPUT."""
    global _watcher_running
    
    # Archivos ya conocidos para evitar re-procesamiento
    known_input = set()
    known_output = set()
    
    while _watcher_running:
        try:
            # Vigilar INPUT (docs nuevos para el Firmante)
            input_dir = get_input_dir()
            if input_dir.exists():
                current_files = set(f.name for f in input_dir.glob("*.pdf") if f.is_file())
                new_files = current_files - known_input
                for fname in new_files:
                    fpath = input_dir / fname
                    if _process_input_file(str(fpath)):
                        if callback_on_change:
                            try: callback_on_change()
                            except: pass
                known_input = current_files
                
            # Vigilar OUTPUT (docs devueltos para el Emisor)
            output_dir = get_output_dir()
            if output_dir.exists():
                current_files = set(f.name for f in output_dir.glob("*.pdf") if f.is_file())
                new_files = current_files - known_output
                for fname in new_files:
                    fpath = output_dir / fname
                    if _process_output_file(str(fpath)):
                        if callback_on_change:
                            try: callback_on_change()
                            except: pass
                known_output = current_files
        except Exception as e:
            print(f"[Watcher] Error: {e}")
                        
        time.sleep(5)

def start_watcher(callback_on_change=None):
    """Inicia la vigilancia dual INPUT/OUTPUT."""
    global _watcher_running, _watcher_thread
    
    input_dir = get_input_dir()
    output_dir = get_output_dir()
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    if _watcher_running:
        return
        
    _watcher_running = True
    _watcher_thread = threading.Thread(target=_watcher_loop, args=(callback_on_change,), daemon=True)
    _watcher_thread.start()
    print(f"[Watcher] Vigilando INPUT={input_dir} | OUTPUT={output_dir}")

def stop_watcher():
    global _watcher_running
    _watcher_running = False
    if _watcher_thread:
        _watcher_thread.join(timeout=2.0)
    print("[Watcher] Detenido.")
