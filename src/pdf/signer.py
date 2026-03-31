import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers
from pyhanko.sign.fields import SigSeedValueSpec, SigSeedValFlags

def estampar_firma(pdf_original_path, firma_img_path, output_dir_backup):
    """
    Toma un PDF original, le estampa la firma en la última página
    y lo guarda en la carpeta de backup.
    Retorna la ruta del archivo firmado.
    """
    if not os.path.exists(pdf_original_path):
        raise FileNotFoundError(f"No se encontró el PDF: {pdf_original_path}")
    
    if not os.path.exists(firma_img_path):
        raise FileNotFoundError(f"No se encontró la imagen de firma: {firma_img_path}")

    # Asegurar que el directorio destino existe
    os.makedirs(output_dir_backup, exist_ok=True)
    
    # Nomenclatura del nuevo archivo
    nombre_base = os.path.basename(pdf_original_path)
    nombre_sin_ext = os.path.splitext(nombre_base)[0]
    nombre_firmado = f"{nombre_sin_ext}_firmado.pdf"
    ruta_salida = os.path.join(output_dir_backup, nombre_firmado)
    
    # Capa temporal con la firma
    temp_watermark = os.path.join(output_dir_backup, "temp_signature.pdf")
    
    try:
        # 1. Crear PDF con solo la firma (fondo transparente)
        # Posición por defecto: en la parte inferior (x=300, y=100)
        c = canvas.Canvas(temp_watermark, pagesize=letter)
        # Dibujar imagen (x, y, width, height) - coord(0,0) es abajo-izquierda
        c.drawImage(firma_img_path, 300, 100, width=150, height=80, mask='auto')
        c.save()
        
        # 2. Leer el PDF original y la marca de agua
        pdf_reader = PdfReader(pdf_original_path)
        watermark_reader = PdfReader(temp_watermark)
        watermark_page = watermark_reader.pages[0]
        
        pdf_writer = PdfWriter()
        
        # 3. Copiar todas las páginas. Solo estampar la firma en la ÚLTIMA página.
        num_paginas = len(pdf_reader.pages)
        for i in range(num_paginas):
            page = pdf_reader.pages[i]
            
            if i == num_paginas - 1:
                # Es la última página, mezclar la firma
                page.merge_page(watermark_page)
                
            pdf_writer.add_page(page)
            
        # 4. Guardar archivo final
        with open(ruta_salida, "wb") as f_out:
            pdf_writer.write(f_out)
            
        return ruta_salida
        
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_watermark):
            os.remove(temp_watermark)

def firmar_digitalmente(pdf_in_path, pfx_path, pfx_password, output_path=None):
    """
    Realiza la firma criptográfica (PKI) de un PDF usando un archivo .pfx
    """
    if not output_path:
        output_path = pdf_in_path # Sobreescribir o usar el mismo si es temporal

    with open(pdf_in_path, 'rb') as inf:
        w = IncrementalPdfFileWriter(inf)
        
        # Cargar el firmante desde el PFX
        with open(pfx_path, 'rb') as pfx_file:
            pfx_data = pfx_file.read()
            
        signer = signers.SimpleSigner.load_pkcs12(
            pfx_data, passphrase=pfx_password.encode()
        )

        # Aplicar la firma digital (invisible en este caso, o podemos añadir un campo)
        with open(output_path, 'wb') as outf:
            signers.pdf_signer.sign_pdf(
                w, signers.pdf_signer.PdfSignatureMetadata(field_name='FirmaDigital'),
                signer=signer, output=outf,
            )
    
    return output_path

def proceso_firma_completa(pdf_original, firma_img, output_dir, pfx_path=None, pfx_pass=None):
    """
    Realiza ambos procesos: Estampado visual + Sello criptográfico
    """
    # 1. Estampado Visual
    ruta_visual = estampar_firma(pdf_original, firma_img, output_dir)
    
    # 2. Si hay certificado, aplicar sello criptográfico
    if pfx_path and os.path.exists(pfx_path) and pfx_pass:
        # Firmamos sobre el archivo que ya tiene el estampado visual
        firmar_digitalmente(ruta_visual, pfx_path, pfx_pass)
        
    return ruta_visual
