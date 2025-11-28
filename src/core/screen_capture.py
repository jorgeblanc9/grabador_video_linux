"""Módulo para captura de pantalla usando mss (Linux-compatible)."""

import mss
import numpy as np
from PIL import Image
from typing import Optional, Tuple, List, Dict
import os


class ScreenCapture:
    """Clase para capturar pantalla usando mss."""
    
    def __init__(self):
        """Inicializar capturador de pantalla."""
        try:
            self.sct = mss.mss()
            self.monitors = self.sct.monitors
            self.has_display = True
        except Exception as e:
            # En WSL sin X11, mss puede fallar
            self.has_display = False
            self.sct = None
            self.monitors = [{'width': 1920, 'height': 1080, 'top': 0, 'left': 0}]
            # No lanzar error aquí, permitir que la aplicación continúe
        
    def get_monitors(self) -> List[Dict]:
        """
        Obtener lista de monitores disponibles.
        
        Returns:
            Lista de diccionarios con información de monitores.
        """
        return self.monitors
    
    def get_primary_monitor(self) -> Dict:
        """
        Obtener monitor principal.
        
        Returns:
            Diccionario con información del monitor principal.
        """
        return self.monitors[0]
    
    def get_screen_size(self, monitor_index: int = 0) -> Tuple[int, int]:
        """
        Obtener tamaño de la pantalla.
        
        Args:
            monitor_index: Índice del monitor (0 = todos, 1+ = monitor específico).
            
        Returns:
            Tupla (ancho, alto).
        """
        if monitor_index == 0:
            # Monitor 0 es "todos los monitores"
            monitor = self.monitors[0]
        else:
            monitor = self.monitors[monitor_index]
        
        return (monitor['width'], monitor['height'])
    
    def capture_full_screen(self, monitor_index: int = 1) -> np.ndarray:
        """
        Capturar pantalla completa.
        
        Args:
            monitor_index: Índice del monitor (1 = primer monitor).
            
        Returns:
            Array numpy con la imagen capturada (BGR para OpenCV).
            
        Raises:
            RuntimeError: Si no hay display disponible (WSL sin X11).
        """
        if not self.has_display or self.sct is None:
            raise RuntimeError(
                "No hay display disponible. En WSL, necesitas configurar X11 forwarding.\n"
                "Instala un servidor X11 en Windows (VcXsrv, Xming) y configura:\n"
                "export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0"
            )
        
        monitor = self.monitors[monitor_index]
        screenshot = self.sct.grab(monitor)
        
        # Convertir a numpy array y luego a BGR para OpenCV
        img = np.array(screenshot)
        # mss devuelve BGRA, convertir a BGR
        if img.shape[2] == 4:
            img = img[:, :, :3]
        
        return img
    
    def capture_region(self, x: int, y: int, width: int, height: int, 
                       monitor_index: int = 1) -> np.ndarray:
        """
        Capturar región específica de la pantalla.
        
        Args:
            x: Coordenada X de la esquina superior izquierda.
            y: Coordenada Y de la esquina superior izquierda.
            width: Ancho de la región.
            height: Alto de la región.
            monitor_index: Índice del monitor.
            
        Returns:
            Array numpy con la imagen capturada (BGR para OpenCV).
            
        Raises:
            RuntimeError: Si no hay display disponible (WSL sin X11).
        """
        if not self.has_display or self.sct is None:
            raise RuntimeError(
                "No hay display disponible. En WSL, necesitas configurar X11 forwarding."
            )
        
        monitor = self.monitors[monitor_index]
        
        # Ajustar coordenadas relativas al monitor
        region = {
            'top': monitor['top'] + y,
            'left': monitor['left'] + x,
            'width': width,
            'height': height
        }
        
        screenshot = self.sct.grab(region)
        img = np.array(screenshot)
        
        # mss devuelve BGRA, convertir a BGR
        if img.shape[2] == 4:
            img = img[:, :, :3]
        
        return img
    
    def capture_to_pil(self, monitor_index: int = 1) -> Image.Image:
        """
        Capturar pantalla y devolver como imagen PIL.
        
        Args:
            monitor_index: Índice del monitor.
            
        Returns:
            Imagen PIL.
        """
        monitor = self.monitors[monitor_index]
        screenshot = self.sct.grab(monitor)
        return Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
    
    def close(self):
        """Cerrar el capturador de pantalla."""
        if hasattr(self, 'sct') and self.sct is not None:
            try:
                self.sct.close()
            except Exception:
                pass

