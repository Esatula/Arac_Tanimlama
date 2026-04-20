import torch
import logging

class DeviceManager:
    """
    Sistemdeki en iyi donanım hızlandırıcıyı (GPU) tespit eder ve yönetir.
    Kullanıcı tercihine göre CPU/GPU geçişini destekler.
    """
    _preference = "GPU" # Varsayılan tercih

    @staticmethod
    def set_preference(pref: str):
        """'GPU' veya 'CPU' olarak tercih belirler."""
        if pref.upper() in ["GPU", "CPU"]:
            DeviceManager._preference = pref.upper()

    @staticmethod
    def is_gpu_available() -> bool:
        """Sistemde herhangi bir GPU hızlandırıcı olup olmadığını kontrol eder."""
        if torch.cuda.is_available():
            return True
        try:
            import torch_directml
            return torch_directml.is_available()
        except ImportError:
            return False

    @staticmethod
    def get_best_device():
        # Kullanıcı CPU istiyorsa doğrudan CPU dön
        if DeviceManager._preference == "CPU":
            return torch.device("cpu")

        # 1. Öncelik: NVIDIA CUDA
        if torch.cuda.is_available():
            return torch.device("cuda")
        
        # 2. Öncelik: AMD/Intel DirectML
        try:
            import torch_directml
            if torch_directml.is_available():
                return torch_directml.device()
        except ImportError:
            pass
            
        return torch.device("cpu")

    @staticmethod
    def get_device_name() -> str:
        """Arayüz göstergesi için kısa isim döner."""
        if DeviceManager._preference == "CPU":
            return "CPU"
        
        # GPU istenmişse ama ulaşılamıyorsa yine CPU yaz
        if not DeviceManager.is_gpu_available():
            return "CPU"
            
        return "GPU"

    @staticmethod
    def get_detailed_name() -> str:
        """Detaylı donanım bilgisini döner."""
        device = DeviceManager.get_best_device()
        if str(device).startswith("cuda"):
            try: return torch.cuda.get_device_name(0)
            except: return "NVIDIA GPU"
        elif "dml" in str(device).lower():
            return "AMD RX 6600 (DirectML)"
        return "İşlemci (CPU)"
