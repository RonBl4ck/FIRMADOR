"""
=============================================================================
SDGF - Test 1b: Automatización de Outlook (Alternativa sin COM directo)
=============================================================================
Versión alternativa que usa COM con manejo del bloqueo de seguridad
corporativa, e incluye alternativa vía línea de comandos.

Si COM falla por la política de seguridad, se intenta:
  1. Abrir Outlook vía subprocess (línea de comandos)
  2. Usar el protocolo mailto: del sistema

IMPORTANTE: El email NO se envía automáticamente.
=============================================================================
"""

import os
import sys
import io
import datetime
import subprocess
import shutil

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def create_dummy_pdf(filepath):
    """Crea un PDF de prueba simple."""
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj

3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj

4 0 obj
<< /Length 178 >>
stream
BT
/F1 24 Tf
100 700 Td
(SDGF - Documento de Prueba) Tj
0 -40 Td
/F1 14 Tf
(Este es un PDF generado automaticamente) Tj
0 -25 Td
(para validar la integracion con Outlook.) Tj
0 -25 Td
(Fecha: """ + datetime.datetime.now().strftime("%Y-%m-%d %H:%M").encode() + b""") Tj
ET
endstream
endobj

5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000496 00000 n 

trailer
<< /Size 6 /Root 1 0 R >>
startxref
573
%%EOF"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(pdf_content)
    print(f"  PDF de prueba creado: {filepath}")
    return filepath


def find_outlook_exe():
    """Busca el ejecutable de Outlook en las rutas comunes."""
    common_paths = [
        r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\OUTLOOK.EXE",
        r"C:\Program Files\Microsoft Office\root\Office15\OUTLOOK.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office15\OUTLOOK.EXE",
    ]
    
    # Also try to find via where command
    try:
        result = subprocess.run(["where", "outlook.exe"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            path = result.stdout.strip().split('\n')[0]
            if os.path.exists(path):
                return path
    except Exception:
        pass
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # Last resort: search in PATH
    outlook_path = shutil.which("outlook")
    if outlook_path:
        return outlook_path
    
    return None


# =========================================================================
# MÉTODO 1: COM Automation (con mejor manejo de errores)
# =========================================================================
def test_com_outlook(pdf_path):
    """Intenta conectar con Outlook via COM."""
    print("\n" + "=" * 60)
    print("  METODO 1: COM Automation (win32com)")
    print("=" * 60)
    
    try:
        import win32com.client
        import pythoncom
        
        # Inicializar COM en modo STA
        pythoncom.CoInitialize()
        
        try:
            # Intentar conectar a instancia existente
            outlook = win32com.client.GetActiveObject("Outlook.Application")
            print("  Conectado a Outlook existente via GetActiveObject")
        except Exception:
            try:
                outlook = win32com.client.Dispatch("Outlook.Application")
                print("  Outlook instanciado via Dispatch")
            except Exception as e:
                print(f"  COM bloqueado por seguridad: {e}")
                return False
        
        namespace = outlook.GetNamespace("MAPI")
        current_user = namespace.CurrentUser.Name
        print(f"  Usuario: {current_user}")
        
        # Listar cuentas
        accounts = namespace.Accounts
        emails = []
        for i in range(accounts.Count):
            account = accounts.Item(i + 1)
            emails.append(account.SmtpAddress)
            print(f"  Cuenta encontrada: {account.SmtpAddress}")
        
        # Crear email de prueba
        print("\n  Creando email de prueba...")
        mail = outlook.CreateItem(0)
        mail.Subject = "[SDGF-TEST] Documento de Prueba - Favor Revisar"
        mail.Body = (
            "SDGF - Sistema Dual de Gestion de Firmas\n"
            "=========================================\n\n"
            "Este es un correo de prueba generado automaticamente.\n"
            "Se adjunta un PDF que requiere revision y firma.\n\n"
            f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "Estado: En Bandeja\n\n"
            "---\n"
            "Este correo es de prueba. NO requiere accion real."
        )
        
        if os.path.exists(pdf_path):
            mail.Attachments.Add(os.path.abspath(pdf_path))
            print(f"  PDF adjuntado: {os.path.basename(pdf_path)}")
        
        mail.Display()
        print("  Email mostrado en Outlook (NO enviado)")
        
        # Leer bandeja
        print("\n  Leyendo bandeja de entrada...")
        inbox = namespace.GetDefaultFolder(6)
        messages = inbox.Items
        messages.Sort("[ReceivedTime]", True)
        print(f"  Total mensajes en bandeja: {messages.Count}")
        
        count = 0
        for msg in messages:
            if count >= 3:
                break
            try:
                subject = msg.Subject[:45] if msg.Subject else "(Sin asunto)"
                sender = msg.SenderName[:20] if msg.SenderName else "?"
                print(f"    {count+1}. {sender} - {subject}")
            except Exception:
                pass
            count += 1
        
        # Crear carpeta Procesados
        print("\n  Verificando carpeta SDGF_Procesados...")
        folder_exists = False
        for folder in inbox.Folders:
            if folder.Name == "SDGF_Procesados":
                folder_exists = True
                print(f"  Carpeta ya existe ({folder.Items.Count} items)")
                break
        
        if not folder_exists:
            inbox.Folders.Add("SDGF_Procesados")
            print("  Carpeta SDGF_Procesados creada")
        
        pythoncom.CoUninitialize()
        return True
        
    except Exception as e:
        print(f"  Error COM: {e}")
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass
        return False


# =========================================================================
# MÉTODO 2: Outlook via línea de comandos
# =========================================================================
def test_cmdline_outlook(pdf_path):
    """Abre Outlook con un nuevo correo via línea de comandos."""
    print("\n" + "=" * 60)
    print("  METODO 2: Outlook via Linea de Comandos")
    print("=" * 60)
    
    outlook_exe = find_outlook_exe()
    
    if not outlook_exe:
        print("  No se encontro OUTLOOK.EXE")
        print("  Buscando via registro de Windows...")
        
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\OUTLOOK.EXE"
            )
            outlook_exe, _ = winreg.QueryValueEx(key, "")
            winreg.CloseKey(key)
        except Exception:
            pass
    
    if outlook_exe and os.path.exists(outlook_exe):
        print(f"  Outlook encontrado: {outlook_exe}")
        
        # Outlook /c ipm.note crea un nuevo email
        # /a adjunta un archivo
        try:
            abs_pdf = os.path.abspath(pdf_path)
            cmd = [
                outlook_exe,
                "/c", "ipm.note",
                "/a", abs_pdf,
            ]
            print(f"  Ejecutando: OUTLOOK.EXE /c ipm.note /a {os.path.basename(pdf_path)}")
            subprocess.Popen(cmd)
            print("  Outlook deberia abrir un nuevo email con adjunto")
            print("  Revisa la ventana de Outlook...")
            return True
        except Exception as e:
            print(f"  Error al lanzar Outlook: {e}")
            return False
    else:
        print("  No se pudo localizar OUTLOOK.EXE")
        return False


# =========================================================================
# MÉTODO 3: Protocolo mailto (sin adjunto pero funcional)
# =========================================================================
def test_mailto():
    """Abre un email via protocolo mailto del sistema."""
    print("\n" + "=" * 60)
    print("  METODO 3: Protocolo mailto (fallback)")
    print("=" * 60)
    
    try:
        subject = "[SDGF-TEST] Prueba via mailto"
        body = "Este correo fue generado por SDGF via protocolo mailto."
        mailto_url = f'mailto:?subject={subject}&body={body}'
        
        os.startfile(mailto_url)
        print("  Email abierto via protocolo mailto")
        print("  NOTA: Este metodo NO permite adjuntar archivos")
        return True
    except Exception as e:
        print(f"  Error mailto: {e}")
        return False


def test_toast():
    """Test de notificación toast."""
    print("\n" + "=" * 60)
    print("  TEST: Notificacion Toast")
    print("=" * 60)
    
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            "SDGF - Test Outlook",
            "Test de Outlook completado. Revisa los resultados.",
            duration=5,
            threaded=True
        )
        print("  Notificacion enviada")
        return True
    except Exception as e:
        print(f"  Error toast: {e}")
        return False


def main():
    print("=" * 60)
    print("  SDGF - Test 1b: Outlook (Multi-Metodo)")
    print(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Crear PDF de prueba
    test_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(os.path.dirname(test_dir), "assets")
    pdf_path = os.path.join(assets_dir, "documento_prueba_SDGF.pdf")
    create_dummy_pdf(pdf_path)
    
    # Backup dir
    backup_dir = "C:/Gestion_Firmas/Backup"
    os.makedirs(backup_dir, exist_ok=True)
    
    results = {}
    
    # Intentar Método 1: COM
    results["COM Automation"] = test_com_outlook(pdf_path)
    
    if not results["COM Automation"]:
        print("\n  COM no funciono. Intentando metodo alternativo...")
        # Intentar Método 2: Command line
        results["Linea de Comandos"] = test_cmdline_outlook(pdf_path)
        
        if not results["Linea de Comandos"]:
            # Método 3: mailto
            results["Mailto"] = test_mailto()
    
    # Toast siempre
    results["Toast Notification"] = test_toast()
    
    # Resumen
    print("\n" + "=" * 60)
    print("  RESUMEN DE RESULTADOS")
    print("=" * 60)
    for test_name, passed in results.items():
        icon = "[OK]" if passed else "[FAIL]"
        print(f"   {icon} {test_name}")
    
    working_method = None
    for method_name, passed in results.items():
        if passed and method_name != "Toast Notification":
            working_method = method_name
            break
    
    if working_method:
        print(f"\n  METODO VIABLE: {working_method}")
        print("  Este metodo se usara en la version final de SDGF")
    else:
        print("\n  Ningun metodo de Outlook funciono.")
        print("  Opciones:")
        print("  1. Pedir a IT que desbloquee Python para Outlook")
        print("  2. Usar Microsoft Graph API (requiere config)")
    
    input("\n  Presiona ENTER para cerrar...")


if __name__ == "__main__":
    main()
