"""Módulo para captura de pantalla usando mss (Linux-compatible)."""

import mss
import numpy as np
from PIL import Image
from typing import Optional, Tuple, List, Dict
import os
import threading


class ScreenCapture:
    """Clase para capturar pantalla usando mss."""
    
    def __init__(self):
        """Inicializar capturador de pantalla."""
        # mss usa threading.local() internamente, necesitamos una instancia por thread
        self._local = threading.local()
        self._monitors = None
        self._has_display = None
        
        # Inicializar en el thread principal para obtener información de monitores
        try:
            sct = mss.mss()
            self._monitors = sct.monitors
            self._has_display = True
            sct.close()
        except Exception as e:
            # En WSL sin X11, mss puede fallar
            self._has_display = False
            self._monitors = [{'width': 1920, 'height': 1080, 'top': 0, 'left': 0}]
            # No lanzar error aquí, permitir que la aplicación continúe
    
    def _get_mss_instance(self):
        """
        Obtener instancia de mss para el thread actual.
        Crea una nueva instancia si no existe en este thread.
        """
        if not hasattr(self._local, 'sct'):
            try:
                self._local.sct = mss.mss()
            except Exception:
                self._local.sct = None
        return self._local.sct
    
    @property
    def monitors(self):
        """Obtener lista de monitores."""
        return self._monitors
    
    @property
    def has_display(self):
        """Verificar si hay display disponible."""
        return self._has_display
        
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
        if not self.has_display:
            raise RuntimeError(
                "No hay display disponible. En WSL, necesitas configurar X11 forwarding.\n"
                "Instala un servidor X11 en Windows (VcXsrv, Xming) y configura:\n"
                "export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0"
            )
        
        sct = self._get_mss_instance()
        if sct is None:
            raise RuntimeError(
                "No se pudo inicializar mss. Verifica la configuración de X11."
            )
        
        monitor = self.monitors[monitor_index]
        screenshot = sct.grab(monitor)
        
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
        if not self.has_display:
            raise RuntimeError(
                "No hay display disponible. En WSL, necesitas configurar X11 forwarding."
            )
        
        sct = self._get_mss_instance()
        if sct is None:
            raise RuntimeError(
                "No se pudo inicializar mss. Verifica la configuración de X11."
            )
        
        monitor = self.monitors[monitor_index]
        
        # Ajustar coordenadas relativas al monitor
        region = {
            'top': monitor['top'] + y,
            'left': monitor['left'] + x,
            'width': width,
            'height': height
        }
        
        screenshot = sct.grab(region)
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
        sct = self._get_mss_instance()
        if sct is None:
            raise RuntimeError(
                "No se pudo inicializar mss. Verifica la configuración de X11."
            )
        
        monitor = self.monitors[monitor_index]
        screenshot = sct.grab(monitor)
        return Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
    
    def close(self):
        """Cerrar el capturador de pantalla."""
        # Cerrar instancias de mss en todos los threads
        if hasattr(self, '_local'):
            if hasattr(self._local, 'sct') and self._local.sct is not None:
                try:
                    self._local.sct.close()
                except Exception:
                    pass

