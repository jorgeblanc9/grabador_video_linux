"""Grabador unificado sin dependencias Windows."""

import platform
from typing import Optional, Tuple
from .screen_capture import ScreenCapture
from .recorder_manager import VideoRecorder


class UnifiedRecorder:
    """Grabador unificado multiplataforma."""
    
    def __init__(self):
        """Inicializar grabador unificado."""
        self.screen_capture = ScreenCapture()
        self.recorder = None
    
    def get_screen_resolution(self, monitor_index: int = 1) -> Tuple[int, int]:
        """
        Obtener resolución de pantalla (multiplataforma).
        
        Args:
            monitor_index: Índice del monitor.
            
        Returns:
            Tupla (ancho, alto).
        """
        return self.screen_capture.get_screen_size(monitor_index)
    
    def get_available_monitors(self) -> list:
        """
        Obtener lista de monitores disponibles.
        
        Returns:
            Lista de diccionarios con información de monitores.
        """
        return self.screen_capture.get_monitors()
    
    def create_recorder(self, fps: int = 30) -> VideoRecorder:
        """
        Crear instancia de grabador.
        
        Args:
            fps: Frames por segundo.
            
        Returns:
            Instancia de VideoRecorder.
        """
        self.recorder = VideoRecorder(fps=fps)
        return self.recorder
    
    def get_system_info(self) -> dict:
        """
        Obtener información del sistema.
        
        Returns:
            Diccionario con información del sistema.
        """
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': platform.python_version(),
            'monitors': len(self.screen_capture.get_monitors()) - 1  # Excluir monitor "all"
        }
    
    def cleanup(self):
        """Limpiar recursos."""
        if self.recorder:
            self.recorder.cleanup()
        if self.screen_capture:
            self.screen_capture.close()

