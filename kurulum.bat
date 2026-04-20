@echo off
chcp 65001 > nul
echo ============================================================
echo      OtoAnaliz Hibrit Sistem (Nomeroff-Net) Kurulumu
echo ============================================================
echo.
echo [1/3] Python 3.11 kontrol ediliyor...
py -3.11 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo HATA: Python 3.11 bulunamadi!
    echo Lutfen https://www.python.org/downloads/release/python-3119/ adresinden
    echo Python 3.11.9 sürümünü yükleyin ve tekrar deneyin.
    pause
    exit /b
)

echo [2/3] Sanal ortam ve ana paketler kuruluyor...
cd /d "%~dp0"
set "VENV_PATH=Modüller\Plaka Okuma 2\venv_plaka2"

if not exist "%VENV_PATH%" (
    py -3.11 -m venv "%VENV_PATH%"
)

"%VENV_PATH%\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools
"%VENV_PATH%\Scripts\python.exe" -m pip install -r gereksinimler.txt

echo.
echo [3/3] Özel modüller (Git üzerinden) kuruluyor...
"%VENV_PATH%\Scripts\python.exe" -m pip install "craft_text_detector @ git+https://github.com/ria-com/craft-text-detector.git"
"%VENV_PATH%\Scripts\python.exe" -m pip install "modelhub_client @ git+https://github.com/ria-com/modelhub-client.git"
"%VENV_PATH%\Scripts\python.exe" -m pip install "PyTurboJPEG @ git+https://github.com/lilohuang/PyTurboJPEG.git"

echo.
echo ============================================================
echo KURULUM TAMAMLANDI!
echo.
echo Uygulamayi baslatmak icin 'baslat_nomeroff.bat' dosyasini
echo kullanabilirsiniz.
echo ============================================================
pause
