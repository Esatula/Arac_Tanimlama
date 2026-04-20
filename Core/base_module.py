import abc
import numpy as np
from typing import Dict, List, Any, Tuple

class BaseModule(abc.ABC):
    """
    Tüm analiz modülleri için temel arayüz (Contract).
    Yeni bir modül eklemek için bu sınıftan türetme yapılması gerekir.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.is_ready = False

    @abc.abstractmethod
    def load(self) -> bool:
        """Modülün modellerini yükler. Başarılıysa True döner."""
        pass

    @abc.abstractmethod
    def process(self, image: np.ndarray, **kwargs) -> Dict[str, Any]:
        """
        Resmi işler ve standart bir Python sözlüğü döner.
        Çıktı Formatı:
        {
            "annotated_image": np.ndarray,
            "results": List[Dict],
            "count": int,
            "status": str
        }
        """
        pass
