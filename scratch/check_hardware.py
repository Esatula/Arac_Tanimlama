import torch
import sys

print("--- Donanım Hızlandırma Kontrolü ---")
print(f"Python Versiyon: {sys.version}")
print(f"PyTorch Versiyon: {torch.__version__}")

cuda_available = torch.cuda.is_available()
print(f"CUDA (NVIDIA) Erişilebilir mi: {cuda_available}")
if cuda_available:
    print(f"CUDA Cihaz Adı: {torch.cuda.get_device_name(0)}")

try:
    import torch_directml
    dml_available = torch_directml.is_available()
    print(f"DirectML (AMD/Intel) Erişilebilir mi: {dml_available}")
    if dml_available:
        print(f"DirectML Cihaz Sayısı: {torch_directml.device_count()}")
except ImportError:
    print("DirectML: torch-directml kütüphanesi yüklü değil.")
