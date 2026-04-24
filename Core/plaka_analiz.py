import re
import cv2
import numpy as np

class PlakaAnalizator:
    def __init__(self):
        # Ayarlardan modülün aktif/pasif durumunu kontrol etmek için bir bayrak
        self.aktif = True

    def durumu_ayarla(self, durum: bool):
        """Modülü açıp kapatmak için kullanılır."""
        self.aktif = durum

    def analiz_et(self, plaka_metni, arka_plan_rengi=None, yazi_rengi=None):
        """
        Plaka metnini ve (varsa) renk bilgilerini alarak plaka tipini döndürür.
        Renk bilgileri (arka_plan_rengi, yazi_rengi) OCR/Görüntü işleme aşamasından 
        'siyah', 'beyaz', 'kirmizi', 'sari', 'yesil', 'mavi' gibi string olarak gelebilir.
        """
        if not self.aktif:
            return None

        # Boşlukları temizle ve büyük harfe çevir
        plaka = plaka_metni.replace(" ", "").upper()

        sonuc = {
            "plaka": plaka,
            "tur": "Özel Sivil Araç",
            "tespit_yontemi": "Yok",
            "ek_bilgi_gerekiyor": False
        }

        # 1. VALİLİK (İl Kodu + 0001, Örn: 340001. Genellikle kırmızı zemin, sarı yazı)
        if re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])0001$", plaka):
            sonuc["tur"] = "Valilik Makam Aracı"
            sonuc["tespit_yontemi"] = "Regex"
            return sonuc

        # 2. TBMM BAŞKANVEKİLLERİ VE MİLLETVEKİLLERİ
        if re.fullmatch(r"^TBMM\d{3}$", plaka):
            sonuc["tur"] = "TBMM (Milletvekili / Başkanvekili)"
            sonuc["tespit_yontemi"] = "Regex"
            return sonuc

        # 3. ASKERİ ARAÇLAR (Sadece 6 rakamdan oluşur, Valilikle karışmaması için Valilikten sonra)
        if re.fullmatch(r"^\d{6}$", plaka):
            sonuc["tur"] = "Askerî Araç"
            sonuc["tespit_yontemi"] = "Regex"
            return sonuc

        # 4. GEÇİCİ KONAKLAMA İZİNLİ YABANCILAR (MA-MZ arası harf grubu)
        if re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])M[A-Z]\d{3,4}$", plaka):
            sonuc["tur"] = "Geçici Konaklama İzinli Yabancı (Suriyeli vb.)"
            sonuc["tespit_yontemi"] = "Regex"
            return sonuc

        # 5. POLİS, JANDARMA, SAHİL GÜVENLİK
        # Polis genelde A harfi ile başlar: 34 A 1234, 34 AA 123.
        # Jandarma JAA-JZZ: 06 JAA 123.
        # Sahil Güvenlik SG: 35 SG 123.
        if re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])A\d{3,5}$", plaka):
            sonuc["tur"] = "Polis Aracı"
            sonuc["tespit_yontemi"] = "Regex"
            # Polis plakalarında zemin genelde mavi, yazı beyaz olur. Ek renk kontrolü de yapılabilir.
            return sonuc
            
        if re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])J[A-Z]{2}\d{3,4}$", plaka):
            sonuc["tur"] = "Jandarma Aracı"
            sonuc["tespit_yontemi"] = "Regex"
            return sonuc
            
        if re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])SG\d{3,4}$", plaka):
            sonuc["tur"] = "Sahil Güvenlik Aracı"
            sonuc["tespit_yontemi"] = "Regex"
            return sonuc

        # 6. DİPLOMATİK ARAÇLAR (Yeşil zemin, CD, CC, CG, CM)
        if re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])C[C|D|G|M]\d{3,4}$", plaka):
            sonuc["tur"] = "Diplomatik Araç"
            sonuc["tespit_yontemi"] = "Regex"
            return sonuc

        # ===== RENKLE AYIRT EDİLMESİ GEREKENLER =====
        # İl Yönetimi, Resmi Hizmetlere Mahsus Araçlar, İş Makineleri ve bazı özel görevli araçlar
        # sivil araçlarla aynı harf-rakam kombinasyonlarını kullanabilirler (Örn: 34 AA 123 hem resmi hem sivil olabilir).
        # Bu yüzden burada görüntü işleme motorundan (YOLO/OpenCV vb.) arka plan ve yazı rengi talep etmeliyiz.
        
        sonuc["tespit_yontemi"] = "Regex (Belirsiz)"
        sonuc["ek_bilgi_gerekiyor"] = True

        if arka_plan_rengi and yazi_rengi:
            arka_plan_rengi = arka_plan_rengi.lower()
            yazi_rengi = yazi_rengi.lower()

            if arka_plan_rengi == "siyah" and yazi_rengi == "beyaz":
                sonuc["tur"] = "Resmî Hizmete Mahsus Araç"
                sonuc["tespit_yontemi"] = "Renk Analizi"
                sonuc["ek_bilgi_gerekiyor"] = False

            elif arka_plan_rengi == "kirmizi" and yazi_rengi == "sari": # Bazen İl Yönetimi, Kaymakam, Rektör, Emniyet Md.
                sonuc["tur"] = "İl Yönetimi / Üst Düzey Protokol"
                sonuc["tespit_yontemi"] = "Renk Analizi"
                sonuc["ek_bilgi_gerekiyor"] = False
                
            elif arka_plan_rengi == "kirmizi" and yazi_rengi == "beyaz":
                sonuc["tur"] = "Rektör, Emniyet Müdürü, Kaymakam (Protokol)"
                sonuc["tespit_yontemi"] = "Renk Analizi"
                sonuc["ek_bilgi_gerekiyor"] = False

            elif arka_plan_rengi == "sari": # Bazı geçici plakalar ve bazen iş makineleri
                sonuc["tur"] = "Geçici Plaka / Olası İş Makinesi"
                sonuc["tespit_yontemi"] = "Renk Analizi"
                sonuc["ek_bilgi_gerekiyor"] = False
                
            elif arka_plan_rengi == "beyaz" and yazi_rengi == "siyah":
                sonuc["tur"] = "Özel (Sivil) Araç"
                sonuc["tespit_yontemi"] = "Renk Analizi"
                sonuc["ek_bilgi_gerekiyor"] = False

        return sonuc

    def renk_cikar(self, img_bgr):
        """
        Plaka resmini (crop) alıp baskın arka plan ve yazı rengini tahmin eder.
        Dönüş: (arka_plan_rengi, yazi_rengi)
        """
        if img_bgr is None or img_bgr.size == 0:
            return None, None
            
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        mean_v = np.mean(v)
        
        # Renk maskeleri
        lower_red1, upper_red1 = np.array([0, 70, 50]), np.array([10, 255, 255])
        lower_red2, upper_red2 = np.array([170, 70, 50]), np.array([180, 255, 255])
        mask_red = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
        red_ratio = cv2.countNonZero(mask_red) / (hsv.shape[0] * hsv.shape[1])
        
        lower_yellow, upper_yellow = np.array([15, 70, 50]), np.array([35, 255, 255])
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        yellow_ratio = cv2.countNonZero(mask_yellow) / (hsv.shape[0] * hsv.shape[1])
        
        lower_blue, upper_blue = np.array([100, 150, 0]), np.array([140, 255, 255])
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        blue_ratio = cv2.countNonZero(mask_blue) / (hsv.shape[0] * hsv.shape[1])
        
        # Çok karanlık -> Siyah Zemin
        if mean_v < 85: 
            return "siyah", "beyaz"
        
        # Kırmızı Zemin (Valilik/Protokol)
        if red_ratio > 0.3:
            if yellow_ratio > 0.05:
                return "kirmizi", "sari"
            return "kirmizi", "beyaz"
            
        # Sarı Zemin (Geçici vs)
        if yellow_ratio > 0.3:
            return "sari", "siyah"
            
        # Mavi Zemin (Polis)
        if blue_ratio > 0.3:
            return "mavi", "beyaz"
            
        # Varsayılan Beyaz Zemin (Sivil)
        return "beyaz", "siyah"

# Kullanım örneği (Eğer dosya doğrudan çalıştırılırsa test etmek için)
if __name__ == "__main__":
    analizator = PlakaAnalizator()
    
    test_plakalar = [
        ("060001", None, None),            # Valilik
        ("TBMM001", None, None),           # TBMM
        ("700123", None, None),            # Askeri
        ("34MA123", None, None),           # Geçici Yabancı
        ("34A12345", None, None),          # Polis
        ("06JAA123", None, None),          # Jandarma
        ("35CD123", None, None),           # Diplomatik
        ("06AA123", "siyah", "beyaz"),     # Resmi Hizmet (Renkli)
        ("34XYZ123", "beyaz", "siyah"),    # Sivil (Renkli)
        ("34ABC123", None, None)           # Sivil (Renksiz - Bilgi gerekecek)
    ]
    
    for plaka, arka_plan, yazi in test_plakalar:
        print(f"Test: {plaka}")
        print(analizator.analiz_et(plaka, arka_plan, yazi))
        print("-" * 40)
