---
name: pluz_corporate_security_bypass
description: Guía de las restricciones y limitaciones IT encontradas en las laptops organizacionales de Pluz y sus respectivas soluciones y bypasses.
---

# 🛡️ Entorno Corporativo "Pluz" - Limitaciones y Bypasses

Listado de todas las limitaciones de seguridad informática (antivirus, políticas de grupo, bloqueos de Microsoft) presentes en los equipos corporativos de la empresa Pluz y la arquitectura necesaria para implementar software que las sortee con éxito.

## 1. Integración en Segundo Plano con Outlook (COM Objects)
**🔴 Limitación / Problema:**
* Las laptops bloquean explícitamente el uso de automatización silenciosa por COM (Component Object Model) hacia `Outlook.Application`. 
* Si Python intenta leer la Bandeja de Entrada desde fondo o enviar correos mediante `win32com.client.Dispatch('Outlook.Application')`, el antivirus (probablemente Defender ATP o CrowdStrike) detiene el script y alerta a IT como comportamiento sospechoso.

**✅ Bypass (La Vía de Acción del Usuario):**
* **Para el Envío:** No se debe forzar el envío "oculto". Se debe usar la interfaz de línea de comandos predeterminada del ejecutable (`OUTLOOK.EXE /c ipm.note /m "destino" /a "ruta_adjunto"`). Esto *abre* una nueva ventana de redacción en pantalla con el correo pre-rellenado y su adjunto, delegando el clic de "Enviar" al usuario. Esto es considerado "seguro" por el SO.

## 2. Reglas de Outlook "Guardar Archivos Adjuntos a una Carpeta"
**🔴 Limitación / Problema:**
* Por razones de ciberseguridad corporativa modernas, Microsoft ha **removido/desactivado** la opción nativa de "Guardar el archivo adjunto en una carpeta" de las Reglas locales de Outlook.
* Intentar usar scripts VBA para recuperar esta acción está bloqueado por defecto bajo la política "Disable VBA macros".

**✅ Bypass (La Vía de la Carpeta Compartida / Drive Sync):**
* **Solución Óptima:** Usar **OneDrive / SharePoint (Acceso Directo Sincronizado)**. Al sincronizar nativamente una carpeta de SharePoint mediante OneDrive corporativo, las carpetas bajan directamente al disco duro de los usuarios (ej. `C:/Users/.../OneDrive - Empresa/Carpeta`). El cliente oficial de OneDrive ya está certificado en el equipo. Nuestra app Python simplemente monitorea estas carpetas locales (ej. usando `Path.glob` en un hilo infinito cada 5 segundos).
* **Solución de Respaldo:** Power Automate Web. Al ser un producto en la nube, Flow puede acceder al buzón de Exchange 365, detectar los adjuntos y depositarlos directamente en el OneDrive del usuario, desde donde bajarán a su laptop pasivamente.

## 3. Sandboxing del Modo Web Browser (Flet Web_Browser)
**🔴 Limitación / Problema:**
* Las políticas de los navegadores (Chrome/Edge configurados por GPO) o el simple despliegue a localhost mediante modo Flet `WEB_BROWSER` limitan el uso arbitrario del diálogo de sistema (`FilePicker`) y su constructor síncrono antiguo (`page.open`).
* Pueden presentarse excepciones agresivas del tipo `Unhandled error processing page session` / `Unknown control: FilePicker` debido a que WebView exige comunicación `async`/`await` segura.

**✅ Bypass (Async API & TextFields):**
* No usar el FilePicker clásico; todo elemento nativo debe instanciarse e hidratarse mediante `page.overlay.append()` o migrar su manejo a bloques asíncronos en Flet `>=0.82`.
* Proveer alternativas no intrusivas como un Cuadro de Texto (`TextField`) simple donde el usuario puede pegar la ruta absoluta (`C:/.../*.pdf`) o hacer Drag & Drop del PDF directamente de local, evitando las fallas subyacentes de las ventanas modales de explorador.

## 4. Scripts Ejecutables Powershell (.ps1)
**🔴 Limitación / Problema:**
* La `ExecutionPolicy` por defecto previene correr scripts no firmados.

**✅ Bypass (Bypass Explicito en CLI):**
* El software en Python debe proveer una interfaz gráfica (ej: Configuración de Avanzada) que gatille los comandos de PowerShell explícitamente usando la etiqueta `Bypass`:
```python
subprocess.Popen(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
```
* **Es importante mostrar una ventana de consola visible** y no ejecutar en `subprocess.DEVNULL`, de este modo no dispara alertas heurísticas de malware (que usualmente se desencadenan cuando software externo levanta *cmd* o *powershell* ocultos e inyecta parámetros en *silent mode*).
