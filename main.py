import os
import sys
import subprocess

def run_app():
    # Mevcut dizin
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Python 3.11 Sanal Ortam Yolu (Venv)
    venv_base = os.path.join(base_dir, ".venv")
    python_exe = os.path.join(venv_base, "Scripts", "python.exe")
    
    # Eğer sanal ortam bulunamazsa (ilk kurulum yapılmadıysa)
    if not os.path.exists(python_exe):
        print("HATA: Sanal ortam bulunamadı!")
        print(f"Lütfen önce 'kurulum.bat' dosyasını çalıştırın veya")
        print(f"'{python_exe}' yolunun doğruluğundan emin olun.")
        input("\nÇıkmak için Enter'a basın...")
        return

    # Uygulama dosyası
    app_script = os.path.join(base_dir, "OtoAnaliz_Pro.py")

    # Eğer şu anki çalışan python zaten venv içindeki python ise direkt çalıştır
    if sys.executable.lower() == python_exe.lower():
        import runpy
        runpy.run_path(app_script, run_name="__main__")
    else:
        # Değilse, venv'deki python ile kendini/uygulamayı yeniden başlat
        print("Doğru ortam (Python 3.11) başlatılıyor...")
        subprocess.run([python_exe, app_script])

if __name__ == "__main__":
    run_app()
