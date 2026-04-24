from flask import Flask, request, jsonify
import os
import cv2
import numpy as np
import base64
import sys
from pathlib import Path

# Modüller/Plaka Okuma 2 dizinini ekle
plaka2_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Modüller', 'Plaka Okuma 2')
sys.path.append(plaka2_dir)

try:
    from plaka_tanima_motoru import detect_and_read_plaka
    PLAKA_AVAILABLE = True
except ImportError as e:
    print(f"Uyarı: Plaka Motoru yüklenemedi: {e}")
    detect_and_read_plaka = None
    PLAKA_AVAILABLE = False

from flask_cors import CORS

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    temp_path = str(Path(os.path.dirname(__file__)) / "temp_upload.jpg")
    file.save(temp_path)
    
    if not PLAKA_AVAILABLE:
        return jsonify({"error": "Gelişmiş Plaka Motoru modülü veya bağımlılıkları eksik. Lütfen venv kurulumunu kontrol edin."}), 500

    # Plaka Motoru ile analiz yap
    # Bu işlem ilk seferde modelleri indireceği için uzun sürebilir.
    ann_img, text, vehicle_count = detect_and_read_plaka(temp_path)
    
    if ann_img is None:
        return jsonify({"error": text}), 500
        
    # Convert image to base64
    _, buffer = cv2.imencode('.jpg', ann_img)
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    
    # Clean up temp file
    try:
        os.remove(temp_path)
    except:
        pass
        
    return jsonify({
        "image": f"data:image/jpeg;base64,{img_b64}", 
        "texts": text, 
        "vehicle_count": vehicle_count,
        "module": "Gelişmiş Plaka Motoru"
    })

if __name__ == "__main__":
    # Not: Gelişmiş Plaka Motoru ağır bir kütüphanedir, modellerin yüklenmesi zaman alabilir.
    app.run(port=5000)
