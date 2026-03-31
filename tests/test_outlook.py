"""
=============================================================================
SDGF - Test 1: Automatización de Outlook con pywin32
=============================================================================
Este script valida que podemos:
  1. Conectar con Outlook via COM
  2. Crear un email con adjunto PDF
  3. Leer la bandeja de entrada filtrando por asunto
  4. Crear/verificar carpeta "Procesados" en Outlook

IMPORTANTE: El email NO se envía automáticamente, solo se muestra en pantalla.
=============================================================================
"""

import os
import sys
import datetime
import tempfile

# --- Verificación de dependencias ---
def check_dependencies():
    """Verifica que las librerías necesarias estén instaladas."""
    missing = []
    try:
        import win32com.client
    except ImportError:
        missing.append("pywin32")
    try:
        from win10toast import ToastNotifier
    except ImportError:
        missing.append("win10toast")
    
    if missing:
        print(f"❌ Librerías faltantes: {', '.join(missing)}")
        print(f"   Instalar con: pip install {' '.join(missing)}")
        sys.exit(1)
    else:
        print("✅ Todas las dependencias están instaladas.")


def create_dummy_pdf(filepath):
    """Crea un PDF de prueba simple sin dependencias externas."""
    # PDF mínimo válido
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
    
    with open(filepath, "wb") as f:
        f.write(pdf_content)
    print(f"📄 PDF de prueba creado: {filepath}")
    return filepath


def test_connect_outlook():
    """Test 1.1: Conectar con Outlook."""
    import win32com.client
    
    print("\n" + "=" * 60)
    print("🔌 TEST 1.1: Conexión con Outlook")
    print("=" * 60)
    
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        namespace = outlook.GetNamespace("MAPI")
        
        # Obtener info del usuario actual
        current_user = namespace.CurrentUser.Name
        print(f"✅ Conectado a Outlook exitosamente")
        print(f"   👤 Usuario actual: {current_user}")
        
        # Obtener dirección de correo
        accounts = namespace.Accounts
        for i in range(accounts.Count):
            account = accounts.Item(i + 1)
            print(f"   📧 Cuenta: {account.SmtpAddress}")
        
        return outlook, namespace
    except Exception as e:
        print(f"❌ Error al conectar con Outlook: {e}")
        print("   Asegúrate de que Outlook está abierto y configurado.")
        return None, None


def test_create_email_with_attachment(outlook, pdf_path):
    """Test 1.2: Crear un email con adjunto PDF (sin enviar)."""
    print("\n" + "=" * 60)
    print("📨 TEST 1.2: Crear Email con Adjunto PDF")
    print("=" * 60)
    
    try:
        mail = outlook.CreateItem(0)  # 0 = olMailItem
        
        # Configurar el email
        mail.Subject = "[SDGF-TEST] Documento de Prueba - Favor Revisar y Firmar"
        mail.Body = (
            "Este es un correo de prueba generado por el Sistema Dual de Gestión de Firmas (SDGF).\n\n"
            "Se adjunta un documento PDF que requiere su revisión y firma.\n\n"
            "---\n"
            f"Fecha de generación: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "Estado: 🔴 En Bandeja\n"
            "---\n\n"
            "Este es un correo de prueba. NO requiere acción real."
        )
        
        # Adjuntar PDF
        if os.path.exists(pdf_path):
            mail.Attachments.Add(pdf_path)
            print(f"   📎 PDF adjuntado: {os.path.basename(pdf_path)}")
        else:
            print(f"   ⚠️ No se encontró el PDF: {pdf_path}")
        
        # Mostrar el email (NO enviar)
        mail.Display()
        
        print("✅ Email creado y mostrado exitosamente")
        print("   ⚠️ El email NO fue enviado automáticamente.")
        print("   👁️ Revisa la ventana de Outlook para verificar.")
        
        return True
    except Exception as e:
        print(f"❌ Error al crear email: {e}")
        return False


def test_read_inbox(namespace):
    """Test 1.3: Leer la bandeja de entrada filtrando por asunto."""
    print("\n" + "=" * 60)
    print("📥 TEST 1.3: Lectura de Bandeja de Entrada")
    print("=" * 60)
    
    try:
        inbox = namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
        messages = inbox.Items
        messages.Sort("[ReceivedTime]", True)  # Más recientes primero
        
        print(f"   📬 Total de mensajes en bandeja: {messages.Count}")
        
        # Mostrar los 5 más recientes
        print(f"\n   📋 Últimos 5 correos recibidos:")
        print(f"   {'─' * 50}")
        count = 0
        for msg in messages:
            if count >= 5:
                break
            try:
                subject = msg.Subject[:50] if msg.Subject else "(Sin asunto)"
                sender = msg.SenderName[:25] if msg.SenderName else "(Desconocido)"
                received = msg.ReceivedTime.strftime("%Y-%m-%d %H:%M") if msg.ReceivedTime else "N/A"
                print(f"   {count+1}. [{received}] {sender} → {subject}")
            except Exception:
                pass
            count += 1
        
        # Buscar correos con asunto SDGF
        print(f"\n   🔍 Buscando correos con asunto '[SDGF'...")
        sdgf_filter = "@SQL=\"urn:schemas:httpmail:subject\" LIKE '%[SDGF%'"
        filtered = inbox.Items.Restrict(sdgf_filter)
        print(f"   📊 Correos SDGF encontrados: {filtered.Count}")
        
        return True
    except Exception as e:
        print(f"❌ Error al leer bandeja: {e}")
        return False


def test_create_processed_folder(namespace):
    """Test 1.4: Crear/verificar carpeta 'Procesados' en Outlook."""
    print("\n" + "=" * 60)
    print("📁 TEST 1.4: Carpeta 'Procesados' en Outlook")
    print("=" * 60)
    
    try:
        inbox = namespace.GetDefaultFolder(6)
        
        # Verificar si la carpeta ya existe
        folder_exists = False
        for folder in inbox.Folders:
            if folder.Name == "SDGF_Procesados":
                folder_exists = True
                print("✅ Carpeta 'SDGF_Procesados' ya existe en la bandeja.")
                print(f"   📊 Contiene {folder.Items.Count} elemento(s)")
                break
        
        if not folder_exists:
            # Crear la carpeta
            new_folder = inbox.Folders.Add("SDGF_Procesados")
            print("✅ Carpeta 'SDGF_Procesados' creada exitosamente en la bandeja.")
        
        return True
    except Exception as e:
        print(f"❌ Error al gestionar carpeta: {e}")
        return False


def test_toast_notification():
    """Test 1.5: Notificación de escritorio."""
    print("\n" + "=" * 60)
    print("🔔 TEST 1.5: Notificación de Escritorio (Toast)")
    print("=" * 60)
    
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            "SDGF - Sistema de Firmas",
            "✅ Test de notificación exitoso.\nEl sistema puede enviar alertas.",
            duration=5,
            threaded=True
        )
        print("✅ Notificación enviada. Revisa la esquina inferior derecha.")
        return True
    except Exception as e:
        print(f"❌ Error en notificación: {e}")
        return False


def main():
    """Ejecuta todos los tests de Outlook."""
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("╔══════════════════════════════════════════════════════════╗")
    print("║   SDGF - Test 1: Automatización Outlook + Notificación ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║   Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<47} ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # Verificar dependencias
    check_dependencies()
    
    # Crear PDF de prueba
    test_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(os.path.dirname(test_dir), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    pdf_path = os.path.join(assets_dir, "documento_prueba_SDGF.pdf")
    create_dummy_pdf(pdf_path)
    
    # Crear carpeta de backup
    backup_dir = "C:/Gestion_Firmas/Backup"
    os.makedirs(backup_dir, exist_ok=True)
    print(f"📂 Carpeta de backup verificada: {backup_dir}")
    
    results = {}
    
    # Test 1.1: Conexión
    outlook, namespace = test_connect_outlook()
    results["Conexión Outlook"] = outlook is not None
    
    if outlook and namespace:
        # Test 1.2: Email con adjunto
        results["Crear Email"] = test_create_email_with_attachment(outlook, pdf_path)
        
        # Test 1.3: Leer bandeja
        results["Leer Bandeja"] = test_read_inbox(namespace)
        
        # Test 1.4: Carpeta Procesados
        results["Carpeta Procesados"] = test_create_processed_folder(namespace)
    else:
        results["Crear Email"] = False
        results["Leer Bandeja"] = False
        results["Carpeta Procesados"] = False
    
    # Test 1.5: Toast
    results["Notificación Toast"] = test_toast_notification()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    for test_name, passed in results.items():
        icon = "✅" if passed else "❌"
        print(f"   {icon} {test_name}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n   Resultado: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n🎉 ¡Todos los tests pasaron! Outlook es viable para SDGF.")
    else:
        print(f"\n⚠️ {total - passed} test(s) fallaron. Revisa los errores arriba.")
    
    input("\n   Presiona ENTER para cerrar...")


if __name__ == "__main__":
    main()
