import os
import sys
import cv2
import numpy as np
from typing import Dict, Any
from Core.base_module import BaseModule

# Kendi bulunduğu dizini path'e ekle (plaka_okuma_nomeroff importu için)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from plaka_okuma_nomeroff import detect_and_read_nomeroff

class NomeroffPlateModule(BaseModule):
    def __init__(self):
        super().__init__(
            name="Nomeroff-Net v4",
            description="High precision vehicle detection and plate recognition engine."
        )

    def load(self) -> bool:
        try:
            from plaka_okuma_nomeroff import get_pipeline, get_vehicle_model
            # Modelleri arka planda hafızaya yükle (Ağır İşlem)
            get_pipeline()
            get_vehicle_model()
            self.is_ready = True
            return True
        except Exception as e:
            print(f"[!] Nomeroff yükleme hatası: {e}")
            return False

    def process(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """
        Girdi resim yolu (path) veya numpy array olabilir. 
        Mevcut fonksiyon dosya yolu beklediği için şimdilik öyle bırakıyoruz.
        """
        run_plates = kwargs.get("run_plates", True)
        
        # Orijinal fonksiyonu çağır
        ann_img, text, count, plate_list, crops = detect_and_read_nomeroff(image_path, run_plates=run_plates)
        
        return {
            "annotated_image": ann_img,
            "text": text,
            "count": count,
            "plates": plate_list,
            "crops": crops,
            "status": "Success" if ann_img is not None else "Error"
        }
