import os
import sys
import threading
import importlib.util
from enum import Enum, auto
from typing import Dict, List, Type, Callable, Optional
from Core.base_module import BaseModule

class ModuleStatus(Enum):
    NOT_LOADED = auto()
    LOADING = auto()
    READY = auto()
    ERROR = auto()

class ModuleManager:
    """
    Modüller klasörünü tarar ve geçerli modülleri asenkron olarak yükler.
    """
    def __init__(self, modules_dir: str):
        self.modules_dir = modules_dir
        self.loaded_modules: Dict[str, BaseModule] = {}
        self.module_statuses: Dict[str, ModuleStatus] = {}
        self.load_threads: Dict[str, threading.Thread] = {}

    def discover_and_load(self, callback: Optional[Callable[[str, ModuleStatus], None]] = None):
        """
        Modülleri keşfeder ve her biri için arka planda bir yükleme işi başlatır.
        """
        if self.modules_dir not in sys.path:
            sys.path.append(self.modules_dir)

        folders = [f for f in os.listdir(self.modules_dir) if os.path.isdir(os.path.join(self.modules_dir, f))]
        
        for folder in folders:
            adapter_file = os.path.join(self.modules_dir, folder, "module_adapter.py")
            if os.path.exists(adapter_file):
                # Her bir modülü ayrı bir thread'de yükle (Performans Artışı)
                t = threading.Thread(target=self._load_module_task, args=(folder, adapter_file, callback), daemon=True)
                t.start()

    def _load_module_task(self, folder: str, adapter_file: str, callback: Optional[Callable] = None):
        try:
            module_name = f"{folder}.module_adapter"
            spec = importlib.util.spec_from_file_location(module_name, adapter_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            
            for attr_name in dir(mod):
                cls = getattr(mod, attr_name)
                if isinstance(cls, type) and issubclass(cls, BaseModule) and cls is not BaseModule:
                    instance = cls()
                    module_id = instance.name
                    
                    self.module_statuses[module_id] = ModuleStatus.LOADING
                    if callback: callback(module_id, ModuleStatus.LOADING)
                    
                    # Ağır model yükleme işlemini yap
                    if instance.load():
                        self.loaded_modules[module_id] = instance
                        self.module_statuses[module_id] = ModuleStatus.READY
                        if callback: callback(module_id, ModuleStatus.READY)
                    else:
                        self.module_statuses[module_id] = ModuleStatus.ERROR
                        if callback: callback(module_id, ModuleStatus.ERROR)
                    break
        except Exception as e:
            print(f"[!] Modül yükleme hatası ({folder}): {e}")

    def get_module(self, name: str) -> Optional[BaseModule]:
        if self.module_statuses.get(name) == ModuleStatus.READY:
            return self.loaded_modules.get(name)
        return None

    def get_status(self, name: str) -> ModuleStatus:
        return self.module_statuses.get(name, ModuleStatus.NOT_LOADED)

    def list_modules(self) -> List[str]:
        return list(self.module_statuses.keys())
