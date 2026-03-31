import os
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12

def generar_certificado_pfx(nombre_comun, organizacional, pais, password, ruta_salida):
    """
    Genera un certificado digital auto-firmado y lo guarda como un archivo .pfx
    """
    # 1. Generar la llave privada
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # 2. Detalles del certificado
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, pais),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organizacional),
        x509.NameAttribute(NameOID.COMMON_NAME, nombre_comun),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.now() - timedelta(days=1)
    ).not_valid_after(
        datetime.now() + timedelta(days=365*2) # 2 años de validez
    ).add_extension(
        x509.SubjectAltName([x509.DNSName("localhost")]),
        critical=False,
    ).sign(private_key, hashes.SHA256())

    # 3. Guardar como PKCS12 (.pfx)
    pfx_data = pkcs12.serialize_key_and_certificates(
        nombre_comun.encode(),
        private_key,
        cert,
        None,
        serialization.BestAvailableEncryption(password.encode())
    )

    with open(ruta_salida, "wb") as f:
        f.write(pfx_data)
    
    return ruta_salida
