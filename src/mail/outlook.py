import os
import subprocess
import shutil

def find_outlook_exe():
    """Busca el ejecutable de Outlook en las rutas comunes."""
    common_paths = [
        r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\OUTLOOK.EXE",
        r"C:\Program Files\Microsoft Office\root\Office15\OUTLOOK.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office15\OUTLOOK.EXE",
    ]
    
    # Intentar con comando 'where'
    try:
        result = subprocess.run(["where", "outlook.exe"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            path = result.stdout.strip().split('\n')[0]
            if os.path.exists(path):
                return path
    except Exception:
        pass
    
    # Fallback a rutas predeterminadas
    for path in common_paths:
        if os.path.exists(path):
            return path
            
    # Último intento en el PATH del sistema
    return shutil.which("outlook")

def send_document(pdf_path, email_dest, subject_text, body_text="Adjunto documento firmado."):
    """
    Despacha un email usando Outlook vía línea de comandos.
    Esto elude la restricción de seguridad COM automatizada.
    
    Nota: OUTLOOK.EXE /c ipm.note /m "destino@mail.com" /a "ruta"
    abre la ventana de nuevo mensaje en pantalla para que el usuario verifique
    y envíe de forma segura (sin que Python tome control del envío oculto).
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF no encontrado para enviar: {pdf_path}")
        
    outlook_exe = find_outlook_exe()
    if not outlook_exe:
        raise FileNotFoundError("No se encontró el ejecutable de Outlook (OUTLOOK.EXE) en el sistema.")
        
    abs_pdf = os.path.abspath(pdf_path)
    
    cmd = [
        outlook_exe,
        "/c", "ipm.note",
        "/m", f"{email_dest}?subject={subject_text}&body={body_text}",
        "/a", abs_pdf
    ]
    
    try:
        # Lanza el proceso sin bloquear la aplicación
        subprocess.Popen(cmd)
        return True
    except Exception as e:
        print(f"Error despachando Outlook CLI: {e}")
        return False
