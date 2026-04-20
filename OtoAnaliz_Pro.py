import customtkinter as ctk
import os
import sys
import json
import threading
import cv2
import datetime
from PIL import Image
from tkinter import filedialog, messagebox
import queue
from Core.module_manager import ModuleStatus

# Mimari Importları
from Core.module_manager import ModuleManager
from Core.device_manager import DeviceManager

# Dizin ayarları
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULLER_DIR = os.path.join(BASE_DIR, "Modüller")
KAYIT_DIR = os.path.join(BASE_DIR, "Kayitlar")

if not os.path.exists(KAYIT_DIR):
    os.makedirs(KAYIT_DIR)

# Modül Yöneticisini Ön Hazırla (Açılışta yükleme yapmaz)
module_manager = ModuleManager(MODULLER_DIR)

# Görünüm Ayarları
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class OtoAnalizPro(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("OtoAnaliz Pro - Akıllı Araç Analiz Merkezi")
        self.geometry("1150x850")

        self.load_config()
        # GPU Tercihini Uygula
        use_gpu_val = self.config["settings"].get("use_gpu", True)
        DeviceManager.set_preference("GPU" if use_gpu_val else "CPU")
        
        self.sidebar_expanded = True
        self.delete_mode = False # Silme modu durumu
        
        self.selected_modules = {
            "vehicle": ctk.BooleanVar(value=True),
            "plate": ctk.BooleanVar(value=True),
            "hidden": ctk.BooleanVar(value=False)
        }
        self.last_result = None 

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Arka planda Modülleri Yükle (Açılışı hızlandırır)
        threading.Thread(target=module_manager.discover_and_load, daemon=True).start()

        # Analiz Kuyruğu ve İşçi Thread'i
        self.analysis_queue = queue.Queue()
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

        # 1. SIDEBAR
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        self.toggle_btn = ctk.CTkButton(self.sidebar_frame, text="☰", width=40, height=40, 
                                        fg_color="transparent", hover_color="#333333",
                                        command=self.toggle_sidebar)
        self.toggle_btn.pack(anchor="nw", padx=10, pady=10)

        self.sidebar_content = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.sidebar_content.pack(fill="both", expand=True)

        self.logo_label = ctk.CTkLabel(self.sidebar_content, text="OTOANALİZ\nMERKEZİ", 
                                       font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=20)

        self.btn_dashboard = self.create_nav_btn("Ana Panel", self.show_dashboard)
        self.btn_analyze_page = self.create_nav_btn("Analiz Et", self.show_general_analysis)
        self.btn_saved = self.create_nav_btn("Kaydedilenler", self.show_saved)

        self.sidebar_bottom = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.sidebar_bottom.pack(side="bottom", fill="x", pady=20)

        self.settings_btn = ctk.CTkButton(self.sidebar_bottom, text="◆", width=40, height=40,
                                          fg_color="#3d3d3d", hover_color="#555555",
                                          command=self.show_settings)
        self.settings_btn.pack(side="right", padx=20)

        self.version_label = ctk.CTkLabel(self.sidebar_bottom, text="version 2.4", font=ctk.CTkFont(size=10))
        self.version_label.pack(side="left", padx=20)

        # 2. MAIN CONTAINER
        self.main_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.selected_file = None
        self.show_dashboard()

    def create_nav_btn(self, text, command):
        btn = ctk.CTkButton(self.sidebar_content, text=text, height=45, 
                            fg_color="transparent", border_width=1, border_color="#444444",
                            hover_color="#333333", command=command)
        btn.pack(pady=10, padx=20, fill="x")
        return btn

    def toggle_sidebar(self):
        if self.sidebar_expanded:
            self.sidebar_frame.configure(width=60)
            self.sidebar_content.pack_forget()
            self.sidebar_bottom.pack_forget()
        else:
            self.sidebar_frame.configure(width=220)
            self.sidebar_content.pack(fill="both", expand=True)
            self.sidebar_bottom.pack(side="bottom", fill="x", pady=20)
        self.sidebar_expanded = not self.sidebar_expanded

    def load_config(self):
        config_path = os.path.join(BASE_DIR, "Arayuz", "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except:
            self.config = {"settings": {"auto_save": False, "tr_format": True, "use_gpu": True}}

    def save_config(self):
        config_path = os.path.join(BASE_DIR, "Arayuz", "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Sistem Paneli", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=30)
        grid_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        grid_frame.pack(expand=True)
        self.create_module_card(grid_frame, "Arac Tanımı", "vehicle", 0, 0)
        self.create_module_card(grid_frame, "Plaka Okuma", "plate", 0, 1)
        self.create_module_card(grid_frame, "*Saklı Özellik*", "hidden", 1, 0)
        ctk.CTkButton(self.main_frame, text="Analize Başla", font=ctk.CTkFont(size=18),
                      width=200, height=50, command=self.show_analysis).pack(pady=40)

    def create_module_card(self, parent, title, var_key, r, c):
        card = ctk.CTkFrame(parent, width=280, height=150, corner_radius=15, border_width=1)
        card.grid(row=r, column=c, padx=15, pady=15)
        card.grid_propagate(False)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=18)).place(relx=0.5, rely=0.4, anchor="center")
        tick = ctk.CTkCheckBox(card, text="", variable=self.selected_modules[var_key])
        tick.place(relx=0.9, rely=0.85, anchor="center")

    def show_module_config(self):
        # Bu metod dashboard'da modül seçimi için kullanılabilir, 
        # ancak şu an show_dashboard bunu karşılıyor.
        self.show_dashboard()

    def show_general_analysis(self):
        """Genel analiz ekranına geçer."""
        self.selected_modules["vehicle"].set(True)
        self.selected_modules["plate"].set(True)
        self.show_analysis()

    def show_analysis(self):
        self.clear_main_frame()
        
        # Üst Panel (Butonlar solda, Cihaz göstergesi sağda)
        self.top_panel = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_panel.pack(fill="x", pady=20, padx=20)
        
        # Butonlar (SOL)
        self.analysis_controls = ctk.CTkFrame(self.top_panel, fg_color="transparent")
        self.analysis_controls.pack(side="left")
        
        self.btn_select = ctk.CTkButton(self.analysis_controls, text="📁 Dosya Seç", width=120, command=self.select_file)
        self.btn_select.pack(side="left", padx=5)
        self.btn_run = ctk.CTkButton(self.analysis_controls, text="🚀 Başlat", fg_color="#2ecc71", width=120, command=self.run_process)
        self.btn_run.pack(side="left", padx=5)
        
        self.btn_cancel = ctk.CTkButton(self.analysis_controls, text="🛑 İptal", fg_color="#e74c3c", width=100, command=self.cancel_analysis)
        self.btn_reset = ctk.CTkButton(self.analysis_controls, text="🔄 Yeni Analiz", fg_color="#3498db", width=120, command=self.reset_analysis)
        self.btn_save = ctk.CTkButton(self.analysis_controls, text="💾 Kaydet", fg_color="#f39c12", width=100, command=self.manual_save)
        
        # Cihaz Göstergesi (SAĞ) - Tıklanabilir
        device_type = DeviceManager.get_device_name()
        badge_bg = "#2ecc71" if device_type == "GPU" else "#3498db"
        
        # CTkLabel yerine CTkButton kullanarak tıklanabilir yaptık
        self.device_badge = ctk.CTkButton(self.top_panel, text=device_type, width=80, height=35,
                                           corner_radius=8, fg_color=badge_bg, hover_color="#27ae60",
                                           text_color="white", font=ctk.CTkFont(size=14, weight="bold"),
                                           command=self.toggle_device_click)
        self.device_badge.pack(side="right", padx=10)

        # İçerik Alanı (Yatay)
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Sol: Görsel Alanı
        self.display_frame = ctk.CTkFrame(self.content_frame, fg_color="#121212", corner_radius=10)
        self.display_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.img_lbl = ctk.CTkLabel(self.display_frame, text="Görsel seçimi bekliyor...")
        self.img_lbl.pack(expand=True)
        
        # Sağ: Çıktı Bilgileri Paneli
        self.results_panel = ctk.CTkFrame(self.content_frame, width=250, fg_color="#1e1e1e", corner_radius=10)
        self.results_panel.pack(side="right", fill="y")
        self.results_panel.pack_propagate(False)
        
        ctk.CTkLabel(self.results_panel, text="Analiz Sonuçları", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
        
        self.lbl_count = ctk.CTkLabel(self.results_panel, text="Araç Sayısı: -", font=ctk.CTkFont(size=14))
        self.lbl_count.pack(pady=5, anchor="w", padx=20)
        
        ctk.CTkLabel(self.results_panel, text="Okunan Plakalar:", font=ctk.CTkFont(size=14, underline=True)).pack(pady=(20, 5), anchor="w", padx=20)
        self.txt_plates = ctk.CTkTextbox(self.results_panel, fg_color="transparent", width=210, height=300)
        self.txt_plates.pack(pady=5, padx=20, fill="both", expand=True)
        self.txt_plates.configure(state="disabled")

        self.status_lbl = ctk.CTkLabel(self.main_frame, text="Hazır", font=ctk.CTkFont(slant="italic"))
        self.status_lbl.pack(pady=5)

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Görsel", "*.jpg *.jpeg *.png")])
        if path:
            self.selected_file = path
            img = Image.open(path)
            img.thumbnail((800, 500))
            self.img_lbl.configure(image=ctk.CTkImage(light_image=img, dark_image=img, size=img.size), text="")

    def run_process(self):
        if not self.selected_file: return
        
        # Hangi modüllerin çalıştırılacağını al
        run_plates = self.selected_modules["plate"].get()
        run_vehicle = self.selected_modules["vehicle"].get()

        # Eğer araç veya plaka modülü seçiliyse durumlarını kontrol et
        if run_vehicle or run_plates:
            nomeroff_status = module_manager.get_status("Nomeroff-Net v4")
            if nomeroff_status == ModuleStatus.LOADING:
                messagebox.showinfo("Sabır...", "Yapay zeka modelleri arka planda yükleniyor. Lütfen birkaç saniye sonra tekrar deneyin.")
                return
            elif nomeroff_status == ModuleStatus.ERROR:
                messagebox.showerror("Hata", "Yapay zeka modelleri yüklenemedi. Lütfen kurulumu kontrol edin.")
                return

        self.btn_run.pack_forget()
        self.btn_select.configure(state="disabled")
        self.btn_cancel.pack(side="left", padx=10)
        
        # Görevi kuyruğa at
        task = {
            "file": self.selected_file,
            "run_plates": run_plates,
            "run_vehicle": run_vehicle
        }
        self.analysis_queue.put(task)

    def _worker_loop(self):
        """Sürekli çalışan işçi döngüsü - Kuyruktan görev alır."""
        while self.is_running:
            try:
                # 1 saniye bekle (CPU'yu yormamak için)
                task = self.analysis_queue.get(timeout=1.0)
                self._execute_analysis(task)
                self.analysis_queue.task_done()
            except queue.Empty:
                continue

    def _execute_analysis(self, task):
        try:
            file_path = task["file"]
            run_plates = task["run_plates"]
            run_vehicle = task["run_vehicle"]

            ann_img = None
            text = ""
            count = 0
            plate_list = []

            # 1. Araç ve Plaka Tanımı
            if run_vehicle or run_plates:
                nomeroff = module_manager.get_module("Nomeroff-Net v4")
                if nomeroff:
                    result = nomeroff.process(file_path, run_plates=run_plates)
                    if ann_img is None: 
                        ann_img = result["annotated_image"]
                    
                    text += f" | {result['text']}" if text else result['text']
                    count = result["count"]
                    plate_list = result["plates"]

            if ann_img is not None:
                self.last_result = {"img": ann_img, "plates": plate_list, "count": count}
                img_rgb = cv2.cvtColor(ann_img, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)
                img_pil.thumbnail((800, 500))
                res_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=img_pil.size)
                
                self.after(0, lambda: self.finish_analysis(res_img, f"Sonuç: {text}"))
            else:
                self.after(0, lambda: messagebox.showinfo("Bilgi", "Lütfen en az bir aktif modül seçin."))
                self.after(0, self.reset_analysis)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Hata", f"İşleme Hatası: {str(e)}"))
            self.after(0, self.reset_analysis)

    def finish_analysis(self, res_img, status):
        self.img_lbl.configure(image=res_img)
        self.status_lbl.configure(text=status)
        self.btn_cancel.pack_forget()
        self.btn_reset.pack(side="left", padx=10)
        
        if hasattr(self, 'lbl_count') and self.last_result:
            count = self.last_result.get('count', 0)
            self.lbl_count.configure(text=f"Araç Sayısı: {count}")
            plates = self.last_result.get('plates', [])
            plate_text = "\n".join([f"• {p}" for p in plates]) if plates else "Bulunamadı"
            self.txt_plates.configure(state="normal")
            self.txt_plates.delete("1.0", "end")
            self.txt_plates.insert("1.0", plate_text)
            self.txt_plates.configure(state="disabled")

        if self.config["settings"]["auto_save"]:
            self.manual_save()
        else:
            self.btn_save.pack(side="left", padx=10)

    def manual_save(self):
        if self.last_result:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            record_id = len([f for f in os.listdir(KAYIT_DIR) if f.endswith(".txt")]) + 1
            folder_name = f"Kayit_{record_id}_{timestamp}"
            img_path = os.path.join(KAYIT_DIR, f"{folder_name}.jpg")
            cv2.imwrite(img_path, self.last_result["img"])
            log_path = os.path.join(KAYIT_DIR, f"{folder_name}.txt")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"Araç Sayısı: {self.last_result['count']}\n")
                for i, p in enumerate(self.last_result["plates"]):
                    f.write(f"araç_{i+1}: {p}\n")
            self.btn_save.pack_forget()

    def cancel_analysis(self):
        # İşçi döngüsünü kapatmıyoruz, sadece kuyruğu temizliyoruz.
        # Bu sayede tıkalı/donuk kalma sorunu önleniyor.
        try:
            with self.analysis_queue.mutex:
                self.analysis_queue.queue.clear()
        except: pass
        self.reset_analysis()

    def reset_analysis(self):
        self.last_result = None
        self.selected_file = None
        self.btn_save.pack_forget()
        self.btn_reset.pack_forget()
        self.btn_cancel.pack_forget()
        self.btn_select.pack(side="left", padx=10)
        self.btn_select.configure(state="normal")
        self.btn_run.pack(side="left", padx=10)
        self.img_lbl.configure(image=None, text="Görsel seçimi bekliyor...")
        if hasattr(self, 'lbl_count'):
            self.lbl_count.configure(text="Araç Sayısı: -")
            self.txt_plates.configure(state="normal")
            self.txt_plates.delete("1.0", "end")
            self.txt_plates.configure(state="disabled")

    # --- KAYDEDİLENLER (SİLME MODU GÜNCELLEMESİ) ---
    def show_saved(self):
        self.clear_main_frame()
        self.delete_mode = False # Reset delete mode

        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=40)
        ctk.CTkLabel(header, text="Kaydedilen Analizler", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        
        self.btn_delete_toggle = ctk.CTkButton(header, text="Sil", fg_color="#e74c3c", command=self.toggle_delete_mode)
        self.btn_delete_toggle.pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="#121212")
        self.scroll_frame.pack(fill="both", expand=True, padx=40, pady=10)
        self.scroll_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.load_gallery()

    def toggle_delete_mode(self):
        self.delete_mode = not self.delete_mode
        if self.delete_mode:
            self.btn_delete_toggle.configure(text="Seçilenleri Onayla ve Sil", fg_color="#c0392b")
        else:
            self.delete_selected()
            self.btn_delete_toggle.configure(text="Sil", fg_color="#e74c3c")
        self.load_gallery()

    def load_gallery(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        self.delete_vars = {}
        files = sorted([f for f in os.listdir(KAYIT_DIR) if f.endswith(".jpg")], reverse=True)
        
        for i, f_name in enumerate(files):
            name_base = f_name.replace(".jpg", "")
            log_path = os.path.join(KAYIT_DIR, name_base + ".txt")
            
            v_count = "?"
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        line = f.readline()
                        if "Araç Sayısı:" in line:
                            v_count = line.split(":")[1].strip()
                except: pass

            card = ctk.CTkFrame(self.scroll_frame, corner_radius=15, border_width=1)
            card.grid(row=i//3, column=i%3, padx=15, pady=15, sticky="nsew")
            
            try:
                img_path = os.path.join(KAYIT_DIR, f_name)
                pil_img = Image.open(img_path)
                pil_img.thumbnail((250, 150))
                ctk_thumb = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                lbl_img = ctk.CTkLabel(card, image=ctk_thumb, text="")
                lbl_img.pack(pady=(10, 0), padx=10)
            except: pass

            bottom_bar = ctk.CTkFrame(card, fg_color="transparent")
            bottom_bar.pack(fill="x", pady=10, padx=10)
            
            # Seçme Tiki (Sadece silme modunda görünür)
            if self.delete_mode:
                var = ctk.BooleanVar()
                self.delete_vars[name_base] = var
                ctk.CTkCheckBox(bottom_bar, text="", variable=var, width=20).pack(side="left")
            
            badge = ctk.CTkFrame(bottom_bar, fg_color="#34495e", corner_radius=5)
            badge.pack(side="left", padx=5)
            ctk.CTkLabel(badge, text=v_count, font=ctk.CTkFont(weight="bold")).pack(padx=5)
            
            ctk.CTkButton(bottom_bar, text="Aç", width=50, height=24, 
                          command=lambda p=img_path: os.startfile(p)).pack(side="right")

    def delete_selected(self):
        deleted_count = 0
        for name, var in self.delete_vars.items():
            if var.get():
                for ext in [".txt", ".jpg"]:
                    path = os.path.join(KAYIT_DIR, name + ext)
                    if os.path.exists(path): os.remove(path)
                deleted_count += 1
        if deleted_count > 0:
            messagebox.showinfo("Bitti", f"{deleted_count} kayıt silindi.")

    def show_settings(self):
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Sistem Ayarları", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=30)
        
        # Oto Kayıt Switch
        auto_save_sw = ctk.CTkSwitch(self.main_frame, text="Oto-Kayıt Analiz", 
                                     command=lambda: self.toggle_setting("auto_save", auto_save_sw))
        auto_save_sw.pack(pady=10)
        if self.config["settings"].get("auto_save"): auto_save_sw.select()

        ctk.CTkButton(self.main_frame, text="Dashboard'a Dön", command=self.show_dashboard).pack(pady=40)

    def toggle_device_click(self):
        """Analiz ekranındaki badge tıklandığında cihaz değiştirir."""
        current_pref = self.config["settings"].get("use_gpu", True)
        new_pref = not current_pref
        
        if new_pref and not DeviceManager.is_gpu_available():
            messagebox.showwarning("Donanım Uyarısı", 
                                 "Ekran kartı (GPU) hızlandırması sisteminizde kullanılamıyor.\n\n"
                                 "Lütfen AMD DirectML veya NVIDIA CUDA sürücülerinin yüklü olduğundan emin olun.")
            return

        self.config["settings"]["use_gpu"] = new_pref
        DeviceManager.set_preference("GPU" if new_pref else "CPU")
        self.save_config()
        
        # Arayüzü güncelle
        self.show_analysis()

    def toggle_setting(self, key, sw):
        self.config["settings"][key] = sw.get()
        self.save_config()

if __name__ == "__main__":
    app = OtoAnalizPro()
    app.mainloop()
