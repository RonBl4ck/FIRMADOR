import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import shutil
import datetime
import threading

from src.db.models import DocumentoService, HistorialService, ConfigService
from src.pdf.signer import proceso_firma_completa
from src.utils.cert_gen import generar_certificado_pfx
from src.services import watcher

# ============================================================================
# CONFIGURACIÓN GLOBAL CTk
# ============================================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg_dark": "#0f0f1a", "bg_card": "#1a1a2e", "bg_card_hover": "#222240",
    "accent_purple": "#7c3aed", "accent_blue": "#3b82f6",
    "text_primary": "#f1f5f9", "text_secondary": "#94a3b8", "text_muted": "#64748b",
    "border": "#2d2d4a", "status_red": "#ef4444", "status_yellow": "#eab308",
    "status_green": "#22c55e", "status_blue": "#3b82f6", "danger": "#dc2626",
}

class SDGFApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("SDGF - Sistema Dual de Gestión de Firmas (Desktop)")
        self.geometry("1100x750")
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Grid layout (1 fila, 1 columna)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, border_width=0)
        self.header_frame.pack(fill="x", padx=0, pady=0)
        
        self.lbl_title = ctk.CTkLabel(self.header_frame, text="SDGF Enterprise", font=ctk.CTkFont(family="Inter", size=20, weight="bold"), text_color=COLORS["text_primary"])
        self.lbl_title.pack(side="left", padx=20, pady=15)
        
        self.lbl_subtitle = ctk.CTkLabel(self.header_frame, text="Carpeta Compartida Activa", font=ctk.CTkFont(family="Inter", size=12), text_color=COLORS["status_green"])
        self.lbl_subtitle.pack(side="right", padx=20, pady=15)

        # Tabview
        self.tabview = ctk.CTkTabview(self, fg_color=COLORS["bg_dark"], segmented_button_fg_color=COLORS["bg_card"], segmented_button_selected_color=COLORS["accent_purple"], segmented_button_selected_hover_color=COLORS["accent_blue"], text_color=COLORS["text_primary"])
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        self.tab_emisor = self.tabview.add("Panel Emisor")
        self.tab_firmante = self.tabview.add("Panel Firmante")
        self.tab_historial = self.tabview.add("Historial")
        self.tab_config = self.tabview.add("Configuración")
        
        # Evento de cambio de tab
        self.tabview.configure(command=self.on_tab_change)
        
        # Inicializar vistas
        self.build_emisor_view()
        self.build_firmante_view()
        self.build_historial_view()
        self.build_config_view()
        
        # Iniciar watcher con callback para refrezcar UI
        watcher.start_watcher(self.schedule_refresh)
        
    def schedule_refresh(self):
        """Llama a refresh de forma segura desde el hilo del watcher al hilo principal de Tkinter."""
        self.after(100, self.refresh_current_view)
        
    def refresh_current_view(self):
        current_tab = self.tabview.get()
        if current_tab == "Panel Emisor":
            self.load_emisor_data()
        elif current_tab == "Panel Firmante":
            self.load_firmante_data()
        elif current_tab == "Historial":
            self.load_historial_data()

    def on_tab_change(self):
        self.refresh_current_view()
        
    def show_snackbar(self, message, is_error=False):
        # En Tkinter nativo, MessageBox es más seguro corporativamente que popups custom complejos
        if is_error:
            messagebox.showerror("Error", message)
        else:
            messagebox.showinfo("SDGF", message)

    # ================================================================
    # VISTA EMISOR
    # ================================================================
    def build_emisor_view(self):
        # Formulario de carga
        self.frm_upload_emisor = ctk.CTkFrame(self.tab_emisor, fg_color=COLORS["bg_card"], corner_radius=10)
        self.frm_upload_emisor.pack(fill="x", padx=10, pady=10)
        
        self.lbl_up_emisor = ctk.CTkLabel(self.frm_upload_emisor, text="Enviar Documento a Firma", font=ctk.CTkFont(weight="bold", size=16), text_color=COLORS["text_primary"])
        self.lbl_up_emisor.grid(row=0, column=0, columnspan=3, padx=20, pady=(20,10), sticky="w")
        
        self.btn_browse_emisor = ctk.CTkButton(self.frm_upload_emisor, text="Buscar PDF...", command=self.browse_emisor_file, fg_color=COLORS["accent_blue"], hover_color=COLORS["accent_purple"])
        self.btn_browse_emisor.grid(row=1, column=0, padx=20, pady=10)
        
        self.txt_path_emisor = ctk.CTkEntry(self.frm_upload_emisor, width=350, state="readonly", text_color=COLORS["text_secondary"])
        self.txt_path_emisor.grid(row=1, column=1, padx=10, pady=10)
        
        self.cmb_cat_emisor = ctk.CTkComboBox(self.frm_upload_emisor, values=["Carta Aprobación", "Carta Observación", "Contrato", "Memorandum", "Otro"], width=180)
        self.cmb_cat_emisor.grid(row=1, column=2, padx=10, pady=10)
        
        self.btn_send_emisor = ctk.CTkButton(self.frm_upload_emisor, text="🚀 Lanzar al Flujo", command=self.do_emisor_upload, fg_color=COLORS["accent_purple"], hover_color=COLORS["accent_blue"])
        self.btn_send_emisor.grid(row=1, column=3, padx=20, pady=10)
        
        # Tabla de seguimiento (Usamos CTkScrollableFrame para simular tabla)
        self.lbl_track = ctk.CTkLabel(self.tab_emisor, text="Seguimiento de Documentos Enviados", font=ctk.CTkFont(weight="bold", size=16), text_color=COLORS["text_primary"])
        self.lbl_track.pack(padx=10, pady=(20, 5), anchor="w")
        
        self.scroll_emisor = ctk.CTkScrollableFrame(self.tab_emisor, fg_color=COLORS["bg_card"])
        self.scroll_emisor.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_emisor_data()

    def browse_emisor_file(self):
        filepath = filedialog.askopenfilename(title="Seleccionar PDF", filetypes=[("Archivos PDF", "*.pdf")])
        if filepath:
            self.txt_path_emisor.configure(state="normal")
            self.txt_path_emisor.delete(0, "end")
            self.txt_path_emisor.insert(0, filepath)
            self.txt_path_emisor.configure(state="readonly")

    def do_emisor_upload(self):
        pdf_path = self.txt_path_emisor.get()
        if not pdf_path:
            self.show_snackbar("Seleccione un archivo PDF primero.", True)
            return
            
        input_dir = str(watcher.get_input_dir())
        os.makedirs(input_dir, exist_ok=True)
        filename = os.path.basename(pdf_path)
        dest_path = os.path.join(input_dir, filename)
        
        if DocumentoService.existe_archivo(filename):
            self.show_snackbar(f"'{filename}' ya existe en el sistema.", True)
            return
            
        shutil.copy2(pdf_path, dest_path)
        
        fecha_ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        doc_id = DocumentoService.agregar_documento(
            nombre=filename, ruta_original=dest_path, remitente="Flujo Emisor", destinatario="Flujo Firmante",
            estado="enviado", categoria=self.cmb_cat_emisor.get(), rol_origen="emisor", fecha_envio=fecha_ahora
        )
        HistorialService.log(doc_id, "Lanzado a carpeta INPUT", "Emisor")
        
        self.txt_path_emisor.configure(state="normal")
        self.txt_path_emisor.delete(0, "end")
        self.txt_path_emisor.configure(state="readonly")
        
        self.show_snackbar(f"Documento '{filename}' enviado a firma.")
        self.load_emisor_data()

    def load_emisor_data(self):
        for widget in self.scroll_emisor.winfo_children():
            widget.destroy()
            
        docs = DocumentoService.get_all("emisor")
        
        # Header (simulado)
        hdr = ctk.CTkFrame(self.scroll_emisor, fg_color="transparent")
        hdr.pack(fill="x", pady=5)
        ctk.CTkLabel(hdr, text="Archivo", width=300, anchor="w", text_color=COLORS["text_muted"]).pack(side="left", padx=10)
        ctk.CTkLabel(hdr, text="Categoría", width=150, anchor="w", text_color=COLORS["text_muted"]).pack(side="left", padx=10)
        ctk.CTkLabel(hdr, text="Fecha Envío", width=150, anchor="center", text_color=COLORS["text_muted"]).pack(side="left", padx=10)
        ctk.CTkLabel(hdr, text="Estado", width=100, anchor="center", text_color=COLORS["text_muted"]).pack(side="left", padx=10)
        
        for d in docs:
            row = ctk.CTkFrame(self.scroll_emisor, fg_color=COLORS["bg_dark"], corner_radius=5)
            row.pack(fill="x", pady=2, padx=5)
            
            ctk.CTkLabel(row, text=d["nombre_archivo"], width=300, anchor="w", text_color=COLORS["text_primary"]).pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(row, text=d.get("categoria") or "N/A", width=150, anchor="w", text_color=COLORS["accent_purple"]).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=d.get("fecha_envio") or "", width=150, anchor="center", text_color=COLORS["text_secondary"]).pack(side="left", padx=10)
            
            estado = d["estado"]
            color = COLORS.get(f"status_{'green' if estado=='finalizado' else 'yellow' if estado=='firmado' else 'red' if estado=='enviado' else 'blue'}", COLORS["text_secondary"])
            lbl_est = ctk.CTkLabel(row, text=estado.upper(), width=100, anchor="center", text_color=color, font=ctk.CTkFont(weight="bold"))
            lbl_est.pack(side="left", padx=10)


    # ================================================================
    # VISTA FIRMANTE
    # ================================================================
    def build_firmante_view(self):
        # Import Manual
        self.frm_import_firm = ctk.CTkFrame(self.tab_firmante, fg_color=COLORS["bg_card"], corner_radius=10)
        self.frm_import_firm.pack(fill="x", padx=10, pady=10)
        
        self.lbl_up_firm = ctk.CTkLabel(self.frm_import_firm, text="Importar PDF Manualmente (Si falla la sincronización)", font=ctk.CTkFont(weight="bold", size=14), text_color=COLORS["text_primary"])
        self.lbl_up_firm.grid(row=0, column=0, columnspan=3, padx=20, pady=(15,10), sticky="w")
        
        self.btn_browse_firm = ctk.CTkButton(self.frm_import_firm, text="Buscar PDF...", command=self.browse_firmante_file, fg_color=COLORS["status_blue"])
        self.btn_browse_firm.grid(row=1, column=0, padx=20, pady=10)
        
        self.txt_path_firm = ctk.CTkEntry(self.frm_import_firm, width=400, state="readonly", text_color=COLORS["text_secondary"])
        self.txt_path_firm.grid(row=1, column=1, padx=10, pady=10)
        
        self.btn_send_firm = ctk.CTkButton(self.frm_import_firm, text="📥 Cargar", command=self.do_firmante_import, fg_color=COLORS["status_blue"])
        self.btn_send_firm.grid(row=1, column=2, padx=20, pady=10)
        
        # Tabla Bandeja
        self.lbl_bandeja = ctk.CTkLabel(self.tab_firmante, text="Bandeja de Entrada", font=ctk.CTkFont(weight="bold", size=16), text_color=COLORS["text_primary"])
        self.lbl_bandeja.pack(padx=10, pady=(20, 5), anchor="w")
        
        self.scroll_firmante = ctk.CTkScrollableFrame(self.tab_firmante, fg_color=COLORS["bg_card"])
        self.scroll_firmante.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_firmante_data()

    def browse_firmante_file(self):
        filepath = filedialog.askopenfilename(title="Seleccionar PDF recibido", filetypes=[("Archivos PDF", "*.pdf")])
        if filepath:
            self.txt_path_firm.configure(state="normal")
            self.txt_path_firm.delete(0, "end")
            self.txt_path_firm.insert(0, filepath)
            self.txt_path_firm.configure(state="readonly")

    def do_firmante_import(self):
        pdf_path = self.txt_path_firm.get()
        if not pdf_path:
            self.show_snackbar("Seleccione un archivo PDF primero.", True)
            return
            
        filename = os.path.basename(pdf_path)
        if DocumentoService.existe_archivo(filename):
            self.show_snackbar(f"'{filename}' ya existe.", True)
            return
            
        input_dir = str(watcher.get_input_dir())
        os.makedirs(input_dir, exist_ok=True)
        dest = os.path.join(input_dir, filename)
        shutil.copy2(pdf_path, dest)
        
        fecha_ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        doc_id = DocumentoService.agregar_documento(nombre=filename, ruta_original=dest, remitente="Importación Manual", destinatario="Firmante", estado="enviado", categoria="Importado", rol_origen="firmante_import", fecha_recibo=fecha_ahora)
        HistorialService.log(doc_id, "Importado manualmente", "Firmante")
        
        self.txt_path_firm.configure(state="normal")
        self.txt_path_firm.delete(0, "end")
        self.txt_path_firm.configure(state="readonly")
        
        self.show_snackbar(f"Documento '{filename}' importado.")
        self.load_firmante_data()
        
    def firmar_doc(self, doc_id, ruta_original):
        firma_path = ConfigService.get("firma_path", "C:/Gestion_Firmas/firma.png")
        pfx_path = ConfigService.get("pfx_path")
        pfx_pass = ConfigService.get("pfx_pass")

        if not os.path.exists(firma_path):
            self.show_snackbar("No hay firma visual configurada. Vaya a Configuración.", True)
            return
        if not os.path.exists(ruta_original):
            self.show_snackbar("El PDF original no se encuentra (puede que se esté sincronizando).", True)
            return
            
        try:
            # Ahora usamos el proceso completo (Visual + Digital si aplica)
            ruta_firmado = proceso_firma_completa(
                ruta_original, firma_path, "C:/Gestion_Firmas/Backup",
                pfx_path=pfx_path, pfx_pass=pfx_pass
            )
            
            output_dir = str(watcher.get_output_dir())
            os.makedirs(output_dir, exist_ok=True)
            nombre_firmado = os.path.basename(ruta_firmado)
            dest_output = os.path.join(output_dir, nombre_firmado)
            shutil.copy2(ruta_firmado, dest_output)
            
            DocumentoService.actualizar_estado(doc_id, "firmado", ruta_firmado)
            HistorialService.log(doc_id, "Firmado (Visual + Digital) y movido a OUTPUT", "Firmante")
            self.show_snackbar(f"Documento firmado con éxito.")
            self.load_firmante_data()
        except Exception as e:
            self.show_snackbar(f"Error al firmar: {str(e)}", True)

    def rechazar_doc(self, doc_id):
        DocumentoService.actualizar_estado(doc_id, "rechazado")
        HistorialService.log(doc_id, "Rechazado", "Firmante")
        self.show_snackbar("Documento devuelto (rechazado).")
        self.load_firmante_data()

    def ver_doc(self, ruta):
        if os.path.exists(ruta):
            os.startfile(ruta)
        else:
            self.show_snackbar("Archivo no encontrado en disco.", True)

    def load_firmante_data(self):
        for widget in self.scroll_firmante.winfo_children():
            widget.destroy()
            
        docs = DocumentoService.get_all("firmante")
        
        hdr = ctk.CTkFrame(self.scroll_firmante, fg_color="transparent")
        hdr.pack(fill="x", pady=5)
        ctk.CTkLabel(hdr, text="Archivo", width=300, anchor="w", text_color=COLORS["text_muted"]).pack(side="left", padx=10)
        ctk.CTkLabel(hdr, text="Estado", width=100, anchor="center", text_color=COLORS["text_muted"]).pack(side="left", padx=10)
        ctk.CTkLabel(hdr, text="Acciones", width=300, anchor="center", text_color=COLORS["text_muted"]).pack(side="right", padx=10)
        
        for d in docs:
            row = ctk.CTkFrame(self.scroll_firmante, fg_color=COLORS["bg_dark"], corner_radius=5)
            row.pack(fill="x", pady=2, padx=5)
            
            ctk.CTkLabel(row, text=d["nombre_archivo"], width=300, anchor="w", text_color=COLORS["text_primary"]).pack(side="left", padx=10, pady=10)
            
            estado = d["estado"]
            color = COLORS.get(f"status_{'green' if estado=='finalizado' else 'yellow' if estado=='firmado' else 'red' if estado=='enviado' else 'blue'}", COLORS["text_secondary"])
            ctk.CTkLabel(row, text=estado.upper(), width=100, anchor="center", text_color=color, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
            
            actions_frame = ctk.CTkFrame(row, fg_color="transparent")
            actions_frame.pack(side="right", padx=10)
            
            if estado == "enviado":
                ctk.CTkButton(actions_frame, text="Ver PDF", width=80, fg_color=COLORS["accent_blue"], command=lambda r=d['ruta_original']: self.ver_doc(r)).pack(side="left", padx=5)
                ctk.CTkButton(actions_frame, text="✍ Firmar", width=80, fg_color=COLORS["status_yellow"], text_color="#000", hover_color="#cda000", command=lambda idx=d['id'], r=d['ruta_original']: self.firmar_doc(idx, r)).pack(side="left", padx=5)
                ctk.CTkButton(actions_frame, text="Rechazar", width=80, fg_color="transparent", border_width=1, border_color=COLORS["status_blue"], text_color=COLORS["status_blue"], command=lambda idx=d['id']: self.rechazar_doc(idx)).pack(side="left", padx=5)
            else:
                ctk.CTkLabel(actions_frame, text="Procesado", text_color=COLORS["text_muted"]).pack(side="right", padx=10)

    # ================================================================
    # VISTA HISTORIAL
    # ================================================================
    def build_historial_view(self):
        self.btn_refresh_hist = ctk.CTkButton(self.tab_historial, text="Actualizar Historial", command=self.load_historial_data, fg_color="transparent", border_width=1, text_color=COLORS["text_primary"])
        self.btn_refresh_hist.pack(pady=10, padx=10, anchor="e")
        
        self.scroll_historial = ctk.CTkScrollableFrame(self.tab_historial, fg_color=COLORS["bg_card"])
        self.scroll_historial.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_historial_data()
        
    def load_historial_data(self):
        for widget in self.scroll_historial.winfo_children():
            widget.destroy()
            
        historial = HistorialService.get_recent(50)
        for item in historial:
            row = ctk.CTkFrame(self.scroll_historial, fg_color=COLORS["bg_dark"], corner_radius=5)
            row.pack(fill="x", pady=2, padx=5)
            
            f_name = item.get("nombre_archivo") or f"Doc #{item['documento_id']}"
            texto = f"[{item['fecha']}] {f_name} — {item['accion']} ({item['usuario']})"
            
            ctk.CTkLabel(row, text=texto, anchor="w", text_color=COLORS["text_primary"]).pack(side="left", padx=15, pady=8, expand=True, fill="x")
            
            ruta = item.get("ruta_backup") or item.get("ruta_original")
            if ruta:
                ctk.CTkButton(row, text="Abrir Archivo", width=100, fg_color=COLORS["accent_purple"], command=lambda r=ruta: self.ver_doc(r)).pack(side="right", padx=10)

    # ================================================================
    # VISTA CONFIGURACIÓN
    # ================================================================
    def build_config_view(self):
        frm_cfg = ctk.CTkFrame(self.tab_config, fg_color=COLORS["bg_card"], corner_radius=10)
        frm_cfg.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frm_cfg, text="Configuración del Sistema", font=ctk.CTkFont(weight="bold", size=18)).pack(pady=(20, 20))
        
        # Rutas Compartidas
        ctk.CTkLabel(frm_cfg, text="Carpeta INPUT (Emisor deposita, Watcher Firmante lee):", anchor="w").pack(fill="x", padx=30, pady=(10,0))
        self.txt_cfg_in = ctk.CTkEntry(frm_cfg, width=600)
        self.txt_cfg_in.insert(0, ConfigService.get("ruta_input", str(watcher.DEFAULT_INPUT)))
        self.txt_cfg_in.pack(padx=30, pady=(0, 15))
        
        ctk.CTkLabel(frm_cfg, text="Carpeta OUTPUT (Firmante deposita, Watcher Emisor lee):", anchor="w").pack(fill="x", padx=30, pady=(10,0))
        self.txt_cfg_out = ctk.CTkEntry(frm_cfg, width=600)
        self.txt_cfg_out.insert(0, ConfigService.get("ruta_output", str(watcher.DEFAULT_OUTPUT)))
        self.txt_cfg_out.pack(padx=30, pady=(0, 15))
        
        ctk.CTkLabel(frm_cfg, text="Ruta de Imagen de Firma (.png):", anchor="w").pack(fill="x", padx=30, pady=(10,0))
        self.txt_cfg_firma = ctk.CTkEntry(frm_cfg, width=600)
        self.txt_cfg_firma.insert(0, ConfigService.get("firma_path", "C:/Gestion_Firmas/firma.png"))
        self.txt_cfg_firma.pack(padx=30, pady=(0, 10))

        # Certificado Digital
        ctk.CTkLabel(frm_cfg, text="Certificado Digital (.pfx):", font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=30, pady=(15,0))
        
        row_cert = ctk.CTkFrame(frm_cfg, fg_color="transparent")
        row_cert.pack(fill="x", padx=30, pady=5)
        
        self.txt_cfg_pfx = ctk.CTkEntry(row_cert, width=450, placeholder_text="Ruta al archivo .pfx")
        self.txt_cfg_pfx.insert(0, ConfigService.get("pfx_path", ""))
        self.txt_cfg_pfx.pack(side="left", padx=(0,10))
        
        self.txt_cfg_pass = ctk.CTkEntry(row_cert, width=140, placeholder_text="Contraseña", show="*")
        self.txt_cfg_pass.insert(0, ConfigService.get("pfx_pass", ""))
        self.txt_cfg_pass.pack(side="left")

        btn_gen_cert = ctk.CTkButton(frm_cfg, text="🛡️ Generar Nuevo Certificado", fg_color=COLORS["accent_purple"], command=self.ui_generar_certificado)
        btn_gen_cert.pack(pady=10)
        
        btn_save = ctk.CTkButton(frm_cfg, text="💾 Guardar Configuración", fg_color=COLORS["status_green"], hover_color="#1e9e4a", command=self.save_config)
        btn_save.pack(pady=10)

    def ui_generar_certificado(self):
        # Diálogo simple para generar el certificado
        dest = filedialog.asksaveasfilename(defaultextension=".pfx", filetypes=[("Certificado PFX", "*.pfx")], initialfile="certificado_firma.pfx")
        if not dest: return
        
        pw = self.txt_cfg_pass.get()
        if not pw:
            self.show_snackbar("Por favor, ingresa una contraseña en el campo de arriba para proteger el certificado.", True)
            return
            
        try:
            generar_certificado_pfx("Firma Digital SDGF", "Empresa", "PE", pw, dest)
            self.txt_cfg_pfx.delete(0, "end")
            self.txt_cfg_pfx.insert(0, dest)
            self.show_snackbar(f"Certificado generado exitosamente en: {dest}")
        except Exception as e:
            self.show_snackbar(f"Error al generar certificado: {str(e)}", True)

    def save_config(self):
        r_in = self.txt_cfg_in.get().strip()
        r_out = self.txt_cfg_out.get().strip()
        firma = self.txt_cfg_firma.get().strip()
        pfx = self.txt_cfg_pfx.get().strip()
        pw = self.txt_cfg_pass.get().strip()
        
        if r_in: 
            os.makedirs(r_in, exist_ok=True)
            ConfigService.set("ruta_input", r_in)
        if r_out: 
            os.makedirs(r_out, exist_ok=True)
            ConfigService.set("ruta_output", r_out)
        if firma: 
            ConfigService.set("firma_path", firma)
        if pfx:
            ConfigService.set("pfx_path", pfx)
        if pw:
            ConfigService.set("pfx_pass", pw)
            
        self.show_snackbar("Configuración guardada. Reinicie SDGF para que el Watcher tome las nuevas rutas.")

def main_app():
    app = SDGFApp()
    app.mainloop()
