<#
.SYNOPSIS
SDGF - Setup Rule Installation
Crea un flujo simple para extraer adjuntos usando herramientas autorizadas IT.
#>

Write-Host "============================================="
Write-Host " SDGF - Asistente de Configuracion de Regla "
Write-Host "============================================="
Write-Host ""
Write-Host "Por politicas de seguridad corporativa (bloqueo COM), SDGF monitorea"
Write-Host "la carpeta local C:\Gestion_Firmas\Bandeja_Entrada."
Write-Host ""
Write-Host "Para automatizar que los correos vayan aqui, configure Outlook:"
Write-Host "1. En Outlook, vaya a Inicio > Reglas > Administrar reglas y alertas."
Write-Host "2. Cree una Nueva Regla: 'Aplicar regla a los mensajes que reciba'."
Write-Host "3. Condicion: 'con ciertas palabras en el asunto' -> palabra: [SDGF]"
Write-Host "4. Condicion extra (opcional): 'que tenga datos adjuntos'."
Write-Host ""
Write-Host "Si posee Power Automate Corporativo, abra flow.microsoft.com"
Write-Host "Plantilla sugerida: 'Guardar adjuntos de correo de Office 365 en una carpeta'."
Write-Host ""

$folderPath = "C:\Gestion_Firmas\Bandeja_Entrada"
if (-Not (Test-Path $folderPath)) {
    New-Item -ItemType Directory -Force -Path $folderPath | Out-Null
    Write-Host "[OK] Creada la carpeta receptora: $folderPath"
} else {
    Write-Host "[OK] La carpeta receptora ya existe: $folderPath"
}

Write-Host ""
Write-Host "Presione una tecla para salir..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
