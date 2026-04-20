# 🚗 OtoAnaliz Pro - Hibrit Araç ve Plaka Tanıma Sistemi

OtoAnaliz Pro, modern yapay zeka tekniklerini (YOLOv8 & Nomeroff-Net v4) kullanarak araç sayımı ve plaka tanıma işlemlerini gerçekleştiren, offline çalışan profesyonel bir masaüstü uygulamasıdır.

## ✨ Öne Çıkan Özellikler

- **Hibrit Analiz Motoru**: YOLOv8 ile yüksek hızlı araç tespiti ve Nomeroff-Net v4 ile gelişmiş plaka okuma.
- **Modern Masaüstü Arayüzü**: `customtkinter` tabanlı, kullanıcı dostu, karanlık mod destekli ve estetik dashboard tasarımı.
- **Modüler Yapı**: Sadece araç sayma veya araç + plaka tanıma modülleri arasında anlık geçiş imkanı.
- **Akıllı Kayıt Sistemi**: Analiz sonuçlarını (görsel ve detaylı log) fiziksel olarak diskte saklama ve otomatik kayıt (Oto-Kayıt) desteği.
- **Görsel Arşiv (Galeri)**: Kaydedilen analizleri thumbnail önizlemeleri ve araç sayısı göstergeleri ile birlikte inceleme/silme.
- **Tamamen Offline**: İlk kurulumdan sonra internet bağlantısı gerektirmeyen veri güvenliği odaklı yapı.

## 🛠️ Kurulum

Sistem, uyumluluk için **Python 3.11** gerektirmektedir.

1. Projeyi bilgisayarınıza klonlayın.
2. `kurulum.bat` dosyasını çalıştırarak sanal ortamı (`venv_plaka2`) ve gerekli tüm kütüphaneleri otomatik olarak kurun.
3. Kurulum tamamlandığında ana dizindeki `main.py` dosyasını kullanarak uygulamayı başlatabilirsiniz.

## 🚀 Kullanım

- **Dashboard**: Analiz yapmak istediğiniz modülleri (Araç Tanımı, Plaka Okuma vb.) seçin.
- **Analiz Et**: Resim yükleyerek analizi başlatın. İşlem sırasında isterseniz iptal edebilir veya sonucun kaydını alabilirsiniz.
- **Kaydedilenler**: Geçmiş analizlerinizi galeri görünümünde inceleyebilir, detaylı loglara (TXT) ulaşabilir veya toplu silme işlemi yapabilirsiniz.
- **Ayarlar**: Otomatik kayıt ve diğer sistem tercihlerini yönetebilirsiniz.

## 📁 Proje Yapısı

- `main.py`: Akıllı uygulama başlatıcı (doğru venv'i otomatik bulur).
- `OtoAnaliz_Pro.py`: Ana masaüstü uygulaması kodu.
- `Modüller/`: Yapay zeka motorları ve köprü yazılımlar.
- `Kayitlar/`: Analiz sonuçlarının saklandığı fiziksel arşiv.
- `Arayuz/`: Konfigürasyon ve web tabanlı alternatif arayüz dosyaları.

## 📄 Lisans
Bu proje özel kullanım ve geliştirme amaçlı tasarlanmıştır.

---
*Geliştirici: Antigravity AI Assistant*
