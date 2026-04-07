# Implementacion de OneDrive / Google Drive / Registro en Hoja

## Objetivo

Este proyecto ya tiene una capa de almacenamiento desacoplada para que la app funcione hoy en modo local y mañana pueda conectarse a:

- `OneDrive / SharePoint` via `Microsoft Graph API`
- `Google Drive` via `Google Drive API`
- `Excel Online` o `Google Sheets` como registro auxiliar

La UI y el flujo principal ya estan listos. La integracion pendiente se concentra en pocos archivos.

---

## Archivos clave

### Almacenamiento de archivos

- [src/services/storage.py](D:\PROGRAMACION\FIRMADOR\src\services\storage.py)

Aqui existen dos backends:

- `LocalFolderStorage`
- `OneDriveApiStorage`

Hoy la app usa `local`.
Para OneDrive, debes implementar `OneDriveApiStorage`.

### Registro auxiliar

- [src/services/registry.py](D:\PROGRAMACION\FIRMADOR\src\services\registry.py)

Hoy escribe un `CSV`.
Aqui puedes agregar:

- `Excel Online`
- `Google Sheets`

### Configuracion y flujo

- [src/services/workflow.py](D:\PROGRAMACION\FIRMADOR\src\services\workflow.py)
- [src/ui/streamlit_app.py](D:\PROGRAMACION\FIRMADOR\src\ui\streamlit_app.py)

La pantalla de configuracion ya guarda campos para OneDrive API.

---

## Opcion recomendada: OneDrive + Excel Online

Si el entorno es corporativo Microsoft 365, esta es la opcion recomendada.

### Flujo esperado

1. `A` sube PDF desde Streamlit.
2. `storage.py` sube el archivo a OneDrive en carpeta `entrada`.
3. Se guarda en base:
   - nombre
   - ruta logica
   - estado
   - zona de firma
4. `Martin` firma o rechaza.
5. `storage.py` sube salida a `firmados` o `rechazados`.
6. `registry.py` opcionalmente refleja el cambio en Excel Online.

---

## Implementacion OneDrive

## 1. Registrar aplicacion en Azure / Entra ID

Necesitas:

- `Tenant ID`
- `Client ID`
- `Client Secret`

Permisos tipicos para Graph:

- `Files.ReadWrite.All`
- `Sites.ReadWrite.All`
- `User.Read`

Dependiendo de politica TI, puede requerir consentimiento de administrador.

---

## 2. Completar configuracion en la app

En la pantalla de configuracion de Streamlit ya existen estos campos:

- `onedrive_tenant_id`
- `onedrive_client_id`
- `onedrive_client_secret`
- `onedrive_drive_id`
- `onedrive_folder_inbox`
- `onedrive_folder_signed`
- `onedrive_folder_rejected`

Luego cambia:

- `storage_mode = onedrive_api`

Si no esta listo Graph todavia, deja:

- `storage_mode = local`

---

## 3. Implementar autenticacion en storage.py

Archivo:

- [src/services/storage.py](D:\PROGRAMACION\FIRMADOR\src\services\storage.py)

Dentro de `OneDriveApiStorage` agrega:

- obtencion de token OAuth2 client credentials
- cabeceras `Authorization: Bearer ...`
- metodos de subida, lectura y movimiento

### Base URL tipica Graph

```text
https://graph.microsoft.com/v1.0
```

### Token endpoint tipico

```text
https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token
```

---

## 4. Metodos que debes implementar

En `OneDriveApiStorage` debes completar:

- `upload(folder, filename, content)`
- `copy_between(source_path, target_folder, target_name=None)`
- `move_between(source_path, target_folder, target_name=None)`
- `read_bytes(path)`
- `exists(path)`

### Recomendacion practica

Usa rutas logicas por carpeta:

- `entrada`
- `firmados`
- `rechazados`

y resuelvelas contra IDs o paths configurados en OneDrive.

---

## 5. Mapeo sugerido de carpetas

En configuracion guarda algo asi:

- `onedrive_folder_inbox = /SDGF/entrada`
- `onedrive_folder_signed = /SDGF/firmados`
- `onedrive_folder_rejected = /SDGF/rechazados`

O, si prefieres, guarda IDs de carpeta.

### Recomendacion

Para comenzar, usa paths.
Cuando todo funcione, si quieres mas robustez, migra a IDs.

---

## Ejemplo de implementacion conceptual para upload

Pseudocodigo:

```python
def upload(self, folder, filename, content):
    remote_folder = self._resolve_remote_folder(folder)
    url = f"{self.base_url}/drives/{drive_id}/root:{remote_folder}/{filename}:/content"
    response = requests.put(url, headers=self._auth_headers(binary=True), data=content)
    response.raise_for_status()
    data = response.json()
    return StoredFile(
        name=data["name"],
        path=data["parentReference"]["path"] + "/" + data["name"],
        storage_id=data["id"],
    )
```

---

## Ejemplo de implementacion conceptual para read_bytes

```python
def read_bytes(self, path):
    url = f"{self.base_url}/drives/{drive_id}/root:{path}:/content"
    response = requests.get(url, headers=self._auth_headers())
    response.raise_for_status()
    return response.content
```

---

## Ejemplo de implementacion conceptual para mover

Graph normalmente mueve con `PATCH` sobre el item:

```python
{
  "parentReference": {"path": "/drives/{drive-id}/root:/SDGF/firmados"},
  "name": "nuevo_nombre.pdf"
}
```

Si prefieres simplicidad inicial:

1. descargar
2. subir al destino
3. borrar origen

Eso no es lo mas elegante, pero funciona bien para MVP.

---

## Fallback si Graph falla

No bloquees la prueba por permisos corporativos.

Usa:

- `storage_mode = local`

y apunta estas carpetas a una carpeta sincronizada local de OneDrive, por ejemplo:

```text
C:\Users\<usuario>\OneDrive - Empresa\SDGF\entrada
C:\Users\<usuario>\OneDrive - Empresa\SDGF\firmados
C:\Users\<usuario>\OneDrive - Empresa\SDGF\rechazados
```

Eso permite validar el flujo completo sin API.

---

## Opcion alternativa: Google Drive

Si prefieres Google:

### APIs a usar

- `Google Drive API`
- `Google Sheets API`

### Credenciales

- service account o OAuth client

### Donde implementarlo

Puedes:

1. agregar una nueva clase en [src/services/storage.py](D:\PROGRAMACION\FIRMADOR\src\services\storage.py)
   - `GoogleDriveStorage`
2. extender `get_storage_backend()`
3. agregar campos de configuracion en [src/ui/streamlit_app.py](D:\PROGRAMACION\FIRMADOR\src\ui\streamlit_app.py)

### Metodos equivalentes

- subir archivo a carpeta Drive
- leer archivo
- copiar o mover entre carpetas
- comprobar existencia

---

## Registro en Excel Online

Archivo:

- [src/services/registry.py](D:\PROGRAMACION\FIRMADOR\src\services\registry.py)

### Opcion 1

Usar `Microsoft Graph` para escribir en una tabla de Excel almacenada en OneDrive o SharePoint.

Recomendacion:

- crear un Excel con una tabla formal
- columnas:
  - `id`
  - `nombre_archivo`
  - `estado`
  - `remitente`
  - `destinatario`
  - `fecha_envio`
  - `fecha_firma`
  - `ruta_original`
  - `ruta_backup`
  - `observaciones`

### Estrategia

Para MVP, no intentes actualizar celdas sueltas complejas.
Es mas simple:

1. leer documentos desde SQLite
2. regenerar hoja o tabla
3. escribir snapshot completo

---

## Registro en Google Sheets

Tambien en:

- [src/services/registry.py](D:\PROGRAMACION\FIRMADOR\src\services\registry.py)

Puedes usar:

- `gspread`
- o cliente oficial de Google

### Estrategia recomendada

Igual que en Excel:

1. tomar snapshot de base
2. limpiar hoja
3. escribir encabezados
4. escribir filas actuales

Esto reduce errores respecto a updates incrementales.

---

## Dependencias sugeridas

Para OneDrive / Excel Online:

```text
requests
msal
```

Para Google Drive / Sheets:

```text
google-api-python-client
google-auth
gspread
```

Para vista previa PDF:

```text
PyMuPDF
Pillow
```

---

## Orden de implementacion recomendado

1. Probar mañana si la laptop corporativa permite `Microsoft Graph`.
2. Si si:
   - completar `OneDriveApiStorage`
   - probar subir, leer y mover un PDF
3. Si no:
   - apuntar modo `local` a carpeta sincronizada de OneDrive
4. Luego:
   - conectar `registry.py` a Excel Online
5. Opcional:
   - agregar backend `google_drive`

---

## Checklist de prueba

### OneDrive

- autentica con credenciales
- lista carpeta
- sube PDF
- descarga PDF
- mueve PDF a `firmados`

### Streamlit

- `A` carga PDF
- define zona de firma
- envia
- `Martin` ve pendiente
- firma
- `A` ve estado actualizado

### Registro

- se genera CSV o snapshot en hoja

---

## Nota final

La app ya esta preparada para esto. La parte importante es que el flujo funcional ya no depende de la implementacion del proveedor.

Solo hay que completar:

- backend de archivos en [src/services/storage.py](D:\PROGRAMACION\FIRMADOR\src\services\storage.py)
- backend de hoja en [src/services/registry.py](D:\PROGRAMACION\FIRMADOR\src\services\registry.py)

Todo lo demas ya deberia seguir funcionando sin tocar la UI principal.
