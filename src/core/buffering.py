"""Sistema de buffers para video y audio."""

import queue
import threading
from typing import Optional
import time


class FrameBuffer:
    """Buffer para frames de video."""
    
    def __init__(self, max_size: int = 100):
        """
        Inicializar buffer de frames.
        
        Args:
            max_size: Tamaño máximo del buffer.
        """
        self.buffer = queue.Queue(maxsize=max_size)
        self.max_size = max_size
        self.total_frames = 0
        self.dropped_frames = 0
    
    def put(self, frame, timestamp: float):
        """
        Agregar frame al buffer.
        
        Args:
            frame: Frame de video.
            timestamp: Timestamp del frame.
        """
        try:
            self.buffer.put((frame, timestamp), block=False)
            self.total_frames += 1
        except queue.Full:
            self.dropped_frames += 1
    
    def get(self, timeout: float = 0.1) -> Optional[tuple]:
        """
        Obtener frame del buffer.
        
        Args:
            timeout: Tiempo de espera.
            
        Returns:
            Tupla (frame, timestamp) o None.
        """
        try:
            return self.buffer.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def size(self) -> int:
        """Obtener tamaño actual del buffer."""
        return self.buffer.qsize()
    
    def clear(self):
        """Limpiar buffer."""
        while not self.buffer.empty():
            try:
                self.buffer.get_nowait()
            except queue.Empty:
                break


class AudioBuffer:
    """Buffer para datos de audio."""
    
    def __init__(self, max_size: int = 200):
        """
        Inicializar buffer de audio.
        
        Args:
            max_size: Tamaño máximo del buffer.
        """
        self.buffer = queue.Queue(maxsize=max_size)
        self.max_size = max_size
        self.total_chunks = 0
        self.dropped_chunks = 0
    
    def put(self, audio_data, timestamp: float):
        """
        Agregar chunk de audio al buffer.
        
        Args:
            audio_data: Datos de audio.
            timestamp: Timestamp del chunk.
        """
        try:
            self.buffer.put((audio_data, timestamp), block=False)
            self.total_chunks += 1
        except queue.Full:
            self.dropped_chunks += 1
    
    def get(self, timeout: float = 0.1) -> Optional[tuple]:
        """
        Obtener chunk de audio del buffer.
        
        Args:
            timeout: Tiempo de espera.
            
        Returns:
            Tupla (audio_data, timestamp) o None.
        """
        try:
            return self.buffer.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def size(self) -> int:
        """Obtener tamaño actual del buffer."""
        return self.buffer.qsize()
    
    def clear(self):
        """Limpiar buffer."""
        while not self.buffer.empty():
            try:
                self.buffer.get_nowait()
            except queue.Empty:
                break

