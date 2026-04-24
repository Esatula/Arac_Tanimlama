#!/bin/bash
echo "============================================================"
echo "     OtoAnaliz Gelişmiş Plaka Tanıma Sistemi Kurulumu"
echo "============================================================"
echo ""

echo "[1/3] Python sürümü kontrol ediliyor..."
if ! command -v python3.11 &> /dev/null; then
    echo "HATA: Python 3.11 bulunamadi!"
    echo "Lutfen Python 3.11 yukleyin ve tekrar deneyin."
    exit 1
fi

echo "[2/3] Sanal ortam ve ana paketler kuruluyor..."
VENV_PATH=".venv"

if [ ! -d "$VENV_PATH" ]; then
    python3.11 -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"

pip install --upgrade pip wheel setuptools
pip install -r gereksinimler.txt

echo ""
echo "[3/3] Ozel moduller (Git uzerinden) kuruluyor..."
pip install "craft_text_detector @ git+https://github.com/ria-com/craft-text-detector.git"
pip install "modelhub_client @ git+https://github.com/ria-com/modelhub-client.git"
pip install "PyTurboJPEG @ git+https://github.com/lilohuang/PyTurboJPEG.git"

echo ""
echo "============================================================"
echo "KURULUM TAMAMLANDI!"
echo ""
echo "Uygulamayi baslatmak icin terminalde:"
echo "python main.py"
echo "komutunu kullanabilirsiniz."
echo "============================================================"
