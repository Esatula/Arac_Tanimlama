import re

class OcrDuzeltici:
    """
    Yapay zeka modellerinin (OCR) harf/rakam okuma hatalarını Türkiye Plaka Formatına göre düzelten araç.
    İstenildiği zaman kolayca devredışı bırakılabilecek şekilde ayrı bir modül olarak tasarlanmıştır.
    """
    
    # Sık yapılan OCR harf/rakam karışıklıkları
    HARFTEN_RAKAMA = {'O': '0', 'Q': '0', 'I': '1', 'L': '1', 'Z': '2', 'S': '5', 'B': '8', 'G': '6'}
    RAKAMDAN_HARFE = {'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B', '6': 'G'}

    @classmethod
    def _cevir_rakama(cls, metin):
        sonuc = ""
        for c in metin:
            sonuc += cls.HARFTEN_RAKAMA.get(c, c) if c.isalpha() else c
        return sonuc

    @classmethod
    def _cevir_harfe(cls, metin):
        sonuc = ""
        for c in metin:
            sonuc += cls.RAKAMDAN_HARFE.get(c, c) if c.isdigit() else c
        return sonuc

    @classmethod
    def duzelt(cls, plaka):
        """
        Gelen hatalı plaka metnini alır ve Türkiye kurallarına göre en mantıklı formata çevirip döndürür.
        """
        # 1. Tüm boşluk ve özel karakterleri temizle
        p = re.sub(r"[^A-Z0-9]", "", str(plaka).upper())
        if len(p) < 5 or len(p) > 9:
            return p # Geçersiz uzunluk, dokunma
            
        # 2. TBMM Formatı Kontrolü (TBM ile başlıyorsa)
        if p.startswith("TBM") or p.startswith("TBMM"):
            # Örn: TBM M 001 -> İlk 4 hane harf olmalı, kalan rakam olmalı
            harf_kismi = cls._cevir_harfe(p[:4])
            rakam_kismi = cls._cevir_rakama(p[4:])
            return harf_kismi + rakam_kismi
            
        # 3. Vali / Askeri Plaka Kontrolü (Neredeyse tamamen rakam olan 6 haneli plakalar)
        # Örn: 8O0001 (5 rakam, 1 harf), 1234S6 vs.
        if len(p) == 6:
            harf_sayisi = sum(c.isalpha() for c in p)
            if harf_sayisi <= 2: # 6 hanenin içinde 1 veya 2 harf varsa bu muhtemelen OCR hatasıdır. (Sivil plakalar 2 harfli olamaz, en azından formattan uymuyor çünkü il kodu vb. var)
                # Türkiye'de sadece 1 harfli sivil plaka yoktur. O yüzden hepsini zorla rakam yapıyoruz.
                # Örn: 8O0001 -> 800001, O6000I -> 060001
                return cls._cevir_rakama(p)

        # 4. Standart Sivil / Resmi Format (İl kodu + Harfler + Sayılar)
        # Sivil plakalar her zaman İL KODU (2 hane) ile başlar.
        il_kodu_ham = p[:2]
        il_kodu_duzeltilmis = cls._cevir_rakama(il_kodu_ham)
        
        # Eğer il kodu düzeltmesi geçerli bir kod ise (01-81) standart sivil plaka düzeltmesi yap
        # '00' geçerli değil, ama 01-81 geçerli. OCR hatası yüzünden I6 -> 16 olmuş olabilir.
        if re.match(r"^(0[1-9]|[1-7][0-9]|8[0-1])$", il_kodu_duzeltilmis):
            kalan_kisim = p[2:]
            
            # Kalan kısmın sonundaki ardışık rakamları bul (Plakanın son haneleri her zaman rakamdır)
            # Sağdan sola doğru git, harf görene kadar rakamdır.
            son_rakamlar = ""
            for i in range(len(kalan_kisim) - 1, -1, -1):
                # Karakteri zorla rakama çevirip kontrol et. Eğer karakter bir harfse ve rakam karşılığı yoksa döngü kırılır.
                # Ancak OCR hatası olma ihtimaline karşı RAKAM KABUL EDİLEBİLECEK harfleri de topla.
                c = kalan_kisim[i]
                if c.isdigit() or c in cls.HARFTEN_RAKAMA:
                    son_rakamlar = cls._cevir_rakama(c) + son_rakamlar
                else:
                    break
            
            # Ortada kalan harf grubu
            orta_harfler_ham = kalan_kisim[:len(kalan_kisim) - len(son_rakamlar)]
            orta_harfler_duzeltilmis = cls._cevir_harfe(orta_harfler_ham)
            
            # Güvenlik kontrolü: Eğer plakanın tamamı sayılara zorlanmışsa ve harf kalmamışsa, bu düzeltme mantıksızdır.
            if len(orta_harfler_duzeltilmis) > 0 and len(son_rakamlar) > 0:
                return il_kodu_duzeltilmis + orta_harfler_duzeltilmis + son_rakamlar

        return p # Hiçbir formata uymuyorsa orjinalini döndür
