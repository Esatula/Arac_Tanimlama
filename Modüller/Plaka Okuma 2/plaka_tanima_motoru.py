import os
import sys
import cv2
import numpy as np

# Path to Gelişmiş Plaka Tanıma
NOMEROFF_NET_DIR = os.path.dirname(os.path.abspath(__file__))
if NOMEROFF_NET_DIR not in sys.path:
    sys.path.insert(0, NOMEROFF_NET_DIR)

import torch
from Core.device_manager import DeviceManager

# PyTorch 2.6+ sürümünde gelen güvenlik kısıtlamasını (weights_only) aşmak için 
# torch.load fonksiyonunu global olarak yamalıyoruz.
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    if 'weights_only' in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

from plaka_motoru import pipeline
from plaka_motoru.tools import unzip

# Pickler modelleri nomeroff_net isminde eğittiği için load aşamasında hata vermemesi adına:
sys.modules['nomeroff_net'] = sys.modules['plaka_motoru']

# Initialize the pipeline
# task: "number_plate_detection_and_reading"
# This will download models on first execution
_n_pipeline = None

def get_pipeline():
    global _n_pipeline
    if _n_pipeline is None:
        print("Gelişmiş Plaka Tanıma Pipeline yükleniyor (ilk çalıştırmada model indirilebilir)...")
        # Aktif cihazı al
        curr_device = DeviceManager.get_best_device()
        dev_str = "cpu"
        if "cuda" in str(curr_device): dev_str = "cuda"
        elif "dml" in str(curr_device): dev_str = "dml"
        
        _n_pipeline = pipeline("number_plate_detection_and_reading", image_loader="opencv", device=dev_str)
    return _n_pipeline

# Initialize YOLOv8 for vehicle counting (like the old system)
_vehicle_model = None

def get_vehicle_model():
    global _vehicle_model
    if _vehicle_model is None:
        from ultralytics import YOLO
        # Using the standard yolov8n for speed and consistency with old system
        _vehicle_model = YOLO("yolov8n.pt")
        # .to(device) yerine predict içinde device=... kullanacağız (Daha kararlı)
    return _vehicle_model

def detect_and_read_plaka(image_path, run_plates=True):
    """
    Hybrid recognition: 
    - Vehicles via YOLOv8 (Blue boxes)
    - Plates via Gelişmiş Plaka Tanıma (Green boxes)
    Returns: annotated_image, full_text, vehicle_count
    """
    try:
        n_pipeline = None
        if run_plates:
            n_pipeline = get_pipeline()
        v_model = get_vehicle_model()
        
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            return None, "Hata: Resim okunamadı.", 0

        annotated_img = img.copy()
        
        # Aktif cihaz bilgisini daha temiz alalım
        curr_device = DeviceManager.get_best_device()
        dev_str = "cpu"
        if "cuda" in str(curr_device): dev_str = "cuda"
        elif "dml" in str(curr_device): dev_str = "dml"

        # Hız Optimizasyonu (FP16): GPU varsa yarı hassasiyet kullan
        is_gpu = "cpu" not in dev_str.lower()
        
        # --- 1. Vehicle Detection ---
        vehicle_ids = [2, 3, 5, 7] # car, motorcycle, bus, truck
        
        # FP16 (half=is_gpu) hızı ciddi artırır, isabeti bozmaz
        with torch.no_grad():
            v_results = v_model.predict(image_path, verbose=False, device=dev_str, half=is_gpu)
            
        vehicle_count = 0
        # Box rengi: Sadece araçsa LACİVERT (BGR: 139, 0, 0), plaka da varsa MAVİ (255, 0, 0)
        box_color = (139, 0, 0) if not run_plates else (255, 0, 0)
        
        for r in v_results:
            for box in r.boxes:
                if int(box.cls[0]) in vehicle_ids and float(box.conf[0]) > 0.3:
                    vehicle_count += 1
                    vx1, vy1, vx2, vy2 = map(int, box.xyxy[0])
                    cv2.rectangle(annotated_img, (vx1, vy1), (vx2, vy2), box_color, 2)
                    cv2.putText(annotated_img, f"Arac_{vehicle_count}", (vx1, max(20, vy1-5)), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

        if not run_plates:
            return annotated_img, f"{vehicle_count} Araç Tespit Edildi.", vehicle_count, []

        # --- 2. Plate Detection & OCR ---
        with torch.no_grad():
            results = n_pipeline([image_path])
        res_unzipped = unzip(results)
        (images, images_bboxs, images_points, images_zones, region_ids, region_names, count_lines, confidences, texts) = res_unzipped
        
        bboxs = images_bboxs[0]
        detected_texts = texts[0]
        final_texts = []
        plate_crops = []
        
        for i, box in enumerate(bboxs):
            # Coordinates
            coords = list(map(int, box[:4]))
            xmin, ymin, xmax, ymax = coords
            
            p_text = detected_texts[i] if i < len(detected_texts) else "???"
            final_texts.append(p_text)
            
            # Crop image for color analysis
            crop = img[max(0, ymin):ymax, max(0, xmin):xmax]
            plate_crops.append(crop)
            
            # Draw plate box in GREEN
            cv2.rectangle(annotated_img, (xmin, ymin), (xmax, ymax), (0, 255, 0), 3)
            cv2.putText(annotated_img, p_text, (xmin, max(30, ymin - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        full_text = " | ".join(final_texts) if final_texts else "Plaka tespit edilemedi."
        
        return annotated_img, full_text, vehicle_count, final_texts, plate_crops
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Gelişmiş Plaka Tanıma Hatası: {str(e)}", 0, [], []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        img_path = sys.argv[1]
        ann, txt, count, texts, crops = detect_and_read_plaka(img_path)
        if ann is not None:
            print(f"Tespit Edilen: {txt}")
            cv2.imshow("Gelişmiş Plaka Tanıma Sonuç", ann)
            cv2.waitKey(0)
        else:
            print(txt)
