"""Gestión de configuración persistente."""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Gestor de configuración."""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Inicializar gestor de configuración.
        
        Args:
            config_file: Archivo de configuración.
        """
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Cargar configuración desde archivo."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception:
                self.config = {}
        else:
            self.config = {}
            self.set_defaults()
    
    def save(self):
        """Guardar configuración en archivo."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def set_defaults(self):
        """Establecer valores por defecto."""
        defaults = {
            'fps': 30,
            'format': 'mp4',
            'quality': 'Alta',
            'sample_rate': 44100,
            'audio_channels': 2,
            'enable_system_audio': False,
            'enable_microphone': False,
            'output_directory': '.',
            'last_audio_device': None,
            'last_region': None
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtener valor de configuración.
        
        Args:
            key: Clave de configuración.
            default: Valor por defecto.
            
        Returns:
            Valor de configuración.
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Establecer valor de configuración.
        
        Args:
            key: Clave de configuración.
            value: Valor a establecer.
        """
        self.config[key] = value
        self.save()
    
    def update(self, updates: Dict[str, Any]):
        """
        Actualizar múltiples valores.
        
        Args:
            updates: Diccionario con valores a actualizar.
        """
        self.config.update(updates)
        self.save()
    
    def reset(self):
        """Restablecer configuración a valores por defecto."""
        self.config = {}
        self.set_defaults()
        self.save()

