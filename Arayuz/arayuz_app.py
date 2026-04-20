import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import os

class OtoAnalizUygulamasi:
    def __init__(self, root):
        self.root = root
        self.root.title("Araç Takibi ve Plaka Tanıma Sistemi")
        self.root.geometry("600x400")
        self.root.configure(bg="#2b2b2b")
        self.root.resizable(False, False)

        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#2b2b2b")
        style.configure("TLabel", background="#2b2b2b", foreground="#ffffff", font=("Helvetica", 11))
        style.configure("Header.TLabel", font=("Helvetica", 16, "bold"), foreground="#00d2ff")
        style.configure("TButton", font=("Helvetica", 10), padding=6)
        
        # Main Frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_label = ttk.Label(main_frame, text="Trafik Analiz Paneli", style="Header.TLabel")
        header_label.pack(pady=(0, 20))

        # File Selection Area
        file_frame = ttk.LabelFrame(main_frame, text="1. Girdi Seçimi", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.file_path_var = tk.StringVar(value="")
        
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=50, state="readonly")
        file_entry.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(file_frame, text="Gözat", command=self.browse_file)
        browse_btn.pack(side=tk.LEFT)

        webcam_btn = ttk.Button(file_frame, text="Kamera (0)", command=self.use_webcam)
        webcam_btn.pack(side=tk.LEFT, padx=(10, 0))

        # Modules Area
        modules_frame = ttk.LabelFrame(main_frame, text="2. İşlem Seçimi", padding="10")
        modules_frame.pack(fill=tk.X, pady=(0, 20))

        track_btn = ttk.Button(modules_frame, text="🚗 Araç Takibi ve Sayımı\n(Video / Kamera)", command=self.run_tracking)
        track_btn.pack(side=tk.LEFT, padx='10', fill=tk.X, expand=True)

        plate_btn = ttk.Button(modules_frame, text="🔢 Plaka Tanıma\n(Resim)", command=self.run_plate)
        plate_btn.pack(side=tk.LEFT, padx='10', fill=tk.X, expand=True)

        # Status and Log
        self.status_var = tk.StringVar(value="Sistem hazır. Lütfen bir dosya seçin veya kamerayı kullanın.")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Helvetica", 10, "italic"), foreground="#8bc34a")
        status_label.pack(pady=10)

        # Base directories - updated since arayuz_app.py is now inside `Arayuz` folder
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.tracking_dir = os.path.join(self.base_dir, "Modüller", "Arac Tanima")
        self.plate_dir = os.path.join(self.base_dir, "Modüller", "Plaka Okuma")

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Girdi Dosyası Seçin",
            filetypes=(("Video veya Resim Dosyaları", "*.mp4 *.avi *.jpg *.jpeg *.png"), ("Tüm Dosyalar", "*.*"))
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.status_var.set(f"Dosya seçildi: {os.path.basename(file_path)}")

    def use_webcam(self):
        self.file_path_var.set("0")
        self.status_var.set("Web kamerası (#0) seçildi.")

    def run_tracking(self):
        input_path = self.file_path_var.get()
        if not input_path:
            messagebox.showwarning("Eksik Girdi", "Lütfen önce bir Gözat düğmesiyle dosya seçin veya Kamerayı aktifleştirin.")
            return
            
        self.status_var.set("Araç takibi başlatılıyor... Lütfen bekleyin.")
        threading.Thread(target=self._exec_tracking, args=(input_path,), daemon=True).start()

    def _exec_tracking(self, input_path):
        main_script = os.path.join(self.tracking_dir, "main.py")
        if not os.path.exists(main_script):
            self.show_error(f"Araç Takibi betiği bulunamadı: {main_script}")
            return
            
        cmd = ["python", main_script, "--input", input_path]
        try:
            subprocess.run(cmd, cwd=self.tracking_dir)
            self.status_var.set("Araç takibi işlemi tamamlandı veya durduruldu.")
        except Exception as e:
            self.show_error(f"Hata oluştu: {str(e)}")

    def run_plate(self):
        input_path = self.file_path_var.get()
        if not input_path:
            messagebox.showwarning("Eksik Girdi", "Lütfen bir resim dosyası seçin (Kamera şu an plaka için desteklenmiyor).")
            return
            
        ext = os.path.splitext(input_path)[1].lower()
        if input_path == "0" or ext in ['.mp4', '.avi', '.mov']:
            messagebox.showwarning("Desteklenmeyen Format", "Şu anki Plaka Tanıma modülü yalnızca tekil resimler (.jpg, .png) üzerinde çalışmaktadır.")
            return

        self.status_var.set("Plaka tespiti yapılıyor... (YOLO ve OCR modelleri yükleniyor)")
        threading.Thread(target=self._exec_plate, args=(input_path,), daemon=True).start()

    def _exec_plate(self, input_path):
        plaka_script = os.path.join(self.plate_dir, "plaka_okuma.py")
        if not os.path.exists(plaka_script):
            self.show_error(f"Plaka Okuma betiği bulunamadı: {plaka_script}\nLütfen yönergelere uyarak oluşturulduğuna emin olun.")
            return
        
        # YOLO Ağırlık Yolu
        model_path = os.path.join(self.plate_dir, "plaka_modeli_v2_best.pt")

        cmd = ["python", plaka_script, "--image", input_path, "--model", model_path]
        try:
            subprocess.run(cmd, cwd=self.plate_dir)
            self.status_var.set("Plaka okuma işlemi tamamlandı.")
        except Exception as e:
            self.show_error(f"Hata oluştu: {str(e)}")

    def show_error(self, message):
        self.root.after(0, lambda: messagebox.showerror("Çalıştırma Hatası", message))
        self.root.after(0, lambda: self.status_var.set("Hata oluştu."))

if __name__ == "__main__":
    root = tk.Tk()
    app = OtoAnalizUygulamasi(root)
    root.mainloop()
