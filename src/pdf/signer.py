import os

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers


def estampar_firma(
    pdf_original_path,
    firma_img_path,
    output_dir_backup,
    *,
    page_index=None,
    x=300,
    y=100,
    width=150,
    height=80,
):
    """
    Estampa la firma visible en una página concreta del PDF.
    Las coordenadas usan el sistema PDF: origen abajo a la izquierda.
    """
    if not os.path.exists(pdf_original_path):
        raise FileNotFoundError(f"No se encontró el PDF: {pdf_original_path}")

    if not os.path.exists(firma_img_path):
        raise FileNotFoundError(f"No se encontró la imagen de firma: {firma_img_path}")

    os.makedirs(output_dir_backup, exist_ok=True)

    nombre_base = os.path.basename(pdf_original_path)
    nombre_sin_ext = os.path.splitext(nombre_base)[0]
    nombre_firmado = f"{nombre_sin_ext}_firmado.pdf"
    ruta_salida = os.path.join(output_dir_backup, nombre_firmado)

    pdf_reader = PdfReader(pdf_original_path)
    num_paginas = len(pdf_reader.pages)
    target_page_index = num_paginas - 1 if page_index is None else max(0, min(int(page_index), num_paginas - 1))
    target_page = pdf_reader.pages[target_page_index]
    page_width = float(target_page.mediabox.width)
    page_height = float(target_page.mediabox.height)

    width = float(width)
    height = float(height)
    x = max(0.0, min(float(x), max(0.0, page_width - width)))
    y = max(0.0, min(float(y), max(0.0, page_height - height)))

    temp_watermark = os.path.join(output_dir_backup, f"temp_signature_{target_page_index}.pdf")

    try:
        signer_canvas = canvas.Canvas(temp_watermark, pagesize=(page_width, page_height))
        signer_canvas.drawImage(firma_img_path, x, y, width=width, height=height, mask="auto")
        signer_canvas.save()

        watermark_reader = PdfReader(temp_watermark)
        watermark_page = watermark_reader.pages[0]

        pdf_writer = PdfWriter()
        for current_index in range(num_paginas):
            page = pdf_reader.pages[current_index]
            if current_index == target_page_index:
                page.merge_page(watermark_page)
            pdf_writer.add_page(page)

        with open(ruta_salida, "wb") as f_out:
            pdf_writer.write(f_out)

        return ruta_salida
    finally:
        if os.path.exists(temp_watermark):
            os.remove(temp_watermark)


def firmar_digitalmente(pdf_in_path, pfx_path, pfx_password, output_path=None):
    """
    Realiza la firma criptográfica (PKI) de un PDF usando un archivo .pfx
    """
    if not output_path:
        output_path = pdf_in_path

    with open(pdf_in_path, "rb") as inf:
        writer = IncrementalPdfFileWriter(inf)

        with open(pfx_path, "rb") as pfx_file:
            pfx_data = pfx_file.read()

        signer = signers.SimpleSigner.load_pkcs12(
            pfx_data,
            passphrase=pfx_password.encode(),
        )

        with open(output_path, "wb") as outf:
            signers.pdf_signer.sign_pdf(
                writer,
                signers.pdf_signer.PdfSignatureMetadata(field_name="FirmaDigital"),
                signer=signer,
                output=outf,
            )

    return output_path


def proceso_firma_completa(
    pdf_original,
    firma_img,
    output_dir,
    pfx_path=None,
    pfx_pass=None,
    *,
    page_index=None,
    x=300,
    y=100,
    width=150,
    height=80,
):
    """
    Realiza ambos procesos: estampado visual y sello criptográfico.
    """
    ruta_visual = estampar_firma(
        pdf_original,
        firma_img,
        output_dir,
        page_index=page_index,
        x=x,
        y=y,
        width=width,
        height=height,
    )

    if pfx_path and os.path.exists(pfx_path) and pfx_pass:
        firmar_digitalmente(ruta_visual, pfx_path, pfx_pass)

    return ruta_visual
