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
        Plaka metnini ve renk bilgilerini alarak Türkiye standartlarına göre plaka tipini döndürür.
        """
        if not self.aktif:
            return None

        # Boşlukları temizle ve büyük harfe çevir
        plaka = plaka_metni.replace(" ", "").upper()
        
        # Renk bilgileri gelmemişse standart beyaz/siyah kabul et
        bg = (arka_plan_rengi or "beyaz").lower()
        fg = (yazi_rengi or "siyah").lower()

        sonuc = {
            "plaka": plaka,
            "tur": "Bilinmeyen Plaka",
            "tespit_yontemi": "Renk + Regex",
            "ek_bilgi_gerekiyor": False
        }

        # 1. DİPLOMATİK ARAÇLAR (Yeşil zemin, Beyaz yazı)
        if bg == "yesil":
            if re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])C[CDGM]\d{3,4}$", plaka):
                sonuc["tur"] = "Diplomatik Araç"
            else:
                sonuc["tur"] = "Diplomatik Araç (Belirsiz Format)"
            return sonuc

        # 2. POLİS / EMNİYET TEŞKİLATI (Mavi zemin, Beyaz yazı)
        if bg == "mavi":
            if re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])A[A-Z]?\d{3,5}$", plaka):
                sonuc["tur"] = "Polis Aracı"
            elif re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])J[A-Z]{2}\d{3,4}$", plaka):
                sonuc["tur"] = "Jandarma Aracı"
            elif re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])SG\d{3,4}$", plaka):
                sonuc["tur"] = "Sahil Güvenlik Aracı"
            else:
                sonuc["tur"] = "Emniyet/Güvenlik Gücü (Özel)"
            return sonuc

        # 3. ÜST DÜZEY PROTOKOL / VALİ (Kırmızı zemin, Sarı yazı)
        if bg == "kirmizi" and fg == "sari":
            if re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])0001$", plaka):
                sonuc["tur"] = "Valilik Makam Aracı"
            elif re.fullmatch(r"^\d{4}$", plaka) or re.fullmatch(r"^TBMM\d{3}$", plaka):
                sonuc["tur"] = "Üst Düzey Protokol / TBMM"
            else:
                sonuc["tur"] = "Üst Düzey Protokol"
            return sonuc

        # 4. PROTOKOL / REKTÖR / KAYMAKAM / EMNİYET MÜD. (Kırmızı zemin, Beyaz yazı)
        if bg == "kirmizi" and fg == "beyaz":
            sonuc["tur"] = "Protokol (Rektör/Emniyet Md./Kaymakam)"
            return sonuc

        # 5. RESMİ ARAÇLAR (Siyah zemin, Beyaz yazı)
        if bg == "siyah" and fg == "beyaz":
            sonuc["tur"] = "Resmi Hizmete Mahsus Araç (Kamu/Belediye/İtfaiye)"
            return sonuc

        # 6. GEÇİCİ / TRANSİT PLAKALAR (Sarı zemin, Siyah yazı)
        if bg == "sari":
            sonuc["tur"] = "Geçici / Transit Araç"
            return sonuc

        # 7. ASKERİ ARAÇLAR (Beyaz zemin, Siyah yazı, 6 rakam)
        if re.fullmatch(r"^\d{6}$", plaka):
            sonuc["tur"] = "Askeri Araç"
            return sonuc

        # 8. GEÇİCİ KONAKLAMA İZİNLİ YABANCILAR (MA-MZ arası harf grubu)
        if re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])M[A-Z]\d{3,4}$", plaka):
            sonuc["tur"] = "Geçici Konaklama İzinli Yabancı (Suriyeli vb.)"
            return sonuc

        # 9. TİCARİ ARAÇLAR (Taksi 'T', Minibüs 'M')
        if re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])T\d{3,4}$", plaka):
            sonuc["tur"] = "Ticari Taksi"
            return sonuc
            
        if re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])M\d{3,4}$", plaka):
            sonuc["tur"] = "Ticari Minibüs"
            return sonuc

        # 10. ÖZEL (SİVİL) ARAÇLAR (Beyaz zemin, Siyah yazı)
        if bg == "beyaz":
            if re.fullmatch(r"^(0[1-9]|[1-7][0-9]|8[0-1])[A-Z]{1,3}\d{2,4}$", plaka):
                sonuc["tur"] = "Özel (Sivil) Araç"
            else:
                sonuc["tur"] = "Özel (Sivil) Araç (Belirsiz Format)"
            return sonuc

        sonuc["tur"] = "Format Dışı / Okunamadı"
        return sonuc

    def renk_cikar(self, img_bgr):
        """
        Plaka resmini (crop) alıp K-Means Clustering ile en baskın 2 rengi (arka_plan, yazi_rengi) bulur.
        Dönüş: (arka_plan_rengi, yazi_rengi)
        """
        if img_bgr is None or img_bgr.size == 0:
            return None, None
            
        # Sadece plakanın merkez kısmına odaklan (çamurluk/çerçeve hatalarını önlemek için)
        h, w = img_bgr.shape[:2]
        crop_h = int(h * 0.15)
        crop_w = int(w * 0.15)
        
        if h > crop_h*2 and w > crop_w*2:
            inner_img = img_bgr[crop_h:h-crop_h, crop_w:w-crop_w]
        else:
            inner_img = img_bgr
            
        pixels = inner_img.reshape(-1, 3).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        K = 2
        try:
            _, labels, centers = cv2.kmeans(pixels, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        except Exception:
            return "beyaz", "siyah" # Fallback
        
        counts = np.bincount(labels.flatten())
        bg_idx = np.argmax(counts)
        fg_idx = 1 - bg_idx
        
        bg_color_bgr = centers[bg_idx]
        fg_color_bgr = centers[fg_idx]
        
        def get_color_name(bgr):
            b, g, r = bgr
            
            # Kırmızı: R değeri çok yüksek, G ve B düşük
            if r > 110 and r > g * 1.5 and r > b * 1.5:
                return "kirmizi"
            # Sarı: R ve G yüksek, B düşük
            if r > 130 and g > 120 and b < 100:
                return "sari"
            # Mavi: B değeri R'den çok yüksek
            if b > 100 and b > r * 1.3 and b > g * 1.1:
                return "mavi"
            # Yeşil: G değeri yüksek
            if g > 100 and g > r * 1.2 and g > b * 1.2:
                return "yesil"
                
            # Parlaklık (Luminance) hesabı ile Siyah/Beyaz ayrımı
            brightness = (0.299 * r + 0.587 * g + 0.114 * b)
            if brightness < 110:
                return "siyah"
            else:
                return "beyaz"

        arka_plan = get_color_name(bg_color_bgr)
        yazi = get_color_name(fg_color_bgr)
        
        return arka_plan, yazi

# Kullanım örneği (Eğer dosya doğrudan çalıştırılırsa test etmek için)
if __name__ == "__main__":
    analizator = PlakaAnalizator()
    
    test_plakalar = [
        ("060001", "kirmizi", "sari"),            # Valilik
        ("TBMM001", "kirmizi", "sari"),           # TBMM
        ("700123", "beyaz", "siyah"),             # Askeri
        ("34MA123", "beyaz", "siyah"),            # Geçici Yabancı
        ("34A12345", "mavi", "beyaz"),            # Polis
        ("06JAA123", "mavi", "beyaz"),            # Jandarma
        ("35CD123", "yesil", "beyaz"),            # Diplomatik
        ("06AA123", "siyah", "beyaz"),            # Resmi Hizmet (Belediye vb)
        ("34XYZ123", "beyaz", "siyah"),           # Sivil
        ("34T1234", "beyaz", "siyah"),            # Ticari Taksi
        ("34M1234", "beyaz", "siyah"),            # Ticari Minibüs
        ("06ABC123", "kirmizi", "beyaz"),         # Rektör / Emniyet Müdürü
        ("06G1234", "sari", "siyah"),             # Geçici Plaka
    ]
    
    for plaka, arka_plan, yazi in test_plakalar:
        print(f"Test: {plaka} ({arka_plan} zemin, {yazi} yazi)")
        print(analizator.analiz_et(plaka, arka_plan, yazi))
        print("-" * 40)
