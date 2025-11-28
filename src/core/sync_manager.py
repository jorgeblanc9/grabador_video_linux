"""Gestor de sincronización entre video y audio."""

import time
from typing import Optional
from .buffering import FrameBuffer, AudioBuffer


class SyncManager:
    """Gestor para sincronizar video y audio."""
    
    def __init__(self, frame_buffer: FrameBuffer, audio_buffer: AudioBuffer):
        """
        Inicializar gestor de sincronización.
        
        Args:
            frame_buffer: Buffer de frames de video.
            audio_buffer: Buffer de chunks de audio.
        """
        self.frame_buffer = frame_buffer
        self.audio_buffer = audio_buffer
        self.start_time = None
        self.video_offset = 0.0
        self.audio_offset = 0.0
    
    def start(self):
        """Iniciar sincronización."""
        self.start_time = time.time()
        self.video_offset = 0.0
        self.audio_offset = 0.0
    
    def get_current_time(self) -> float:
        """
        Obtener tiempo actual desde el inicio.
        
        Returns:
            Tiempo en segundos.
        """
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time
    
    def get_next_frame(self, target_time: Optional[float] = None) -> Optional[tuple]:
        """
        Obtener siguiente frame sincronizado.
        
        Args:
            target_time: Tiempo objetivo (None = tiempo actual).
            
        Returns:
            Tupla (frame, timestamp) o None.
        """
        if target_time is None:
            target_time = self.get_current_time()
        
        # Buscar frame más cercano al tiempo objetivo
        best_frame = None
        best_diff = float('inf')
        
        # Revisar algunos frames del buffer
        temp_frames = []
        for _ in range(min(10, self.frame_buffer.size())):
            frame_data = self.frame_buffer.get(timeout=0.01)
            if frame_data:
                frame, timestamp = frame_data
                diff = abs(timestamp - target_time)
                if diff < best_diff:
                    best_diff = diff
                    best_frame = (frame, timestamp)
                temp_frames.append((frame, timestamp))
        
        # Devolver frames no usados al buffer
        for frame_data in temp_frames:
            if frame_data != best_frame:
                self.frame_buffer.put(frame_data[0], frame_data[1])
        
        return best_frame
    
    def get_next_audio(self, target_time: Optional[float] = None) -> Optional[tuple]:
        """
        Obtener siguiente chunk de audio sincronizado.
        
        Args:
            target_time: Tiempo objetivo (None = tiempo actual).
            
        Returns:
            Tupla (audio_data, timestamp) o None.
        """
        if target_time is None:
            target_time = self.get_current_time()
        
        # Obtener chunk más cercano
        audio_data = self.audio_buffer.get(timeout=0.01)
        return audio_data
    
    def reset(self):
        """Reiniciar sincronización."""
        self.start_time = None
        self.video_offset = 0.0
        self.audio_offset = 0.0

