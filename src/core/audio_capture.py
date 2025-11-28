"""Módulo para captura de audio usando PyAudio."""

import os
import sys
import warnings

# Suprimir warnings de ALSA ANTES de importar PyAudio
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings('ignore', category=UserWarning)

# Configurar ALSA para suprimir mensajes (solo funciona parcialmente)
# La mejor solución es redirigir stderr al ejecutar la aplicación
import pyaudio

import numpy as np
from typing import List, Dict, Optional, Callable
import threading
import queue
import time
import os
import warnings
from ..utils.logger import get_logger

# Suprimir warnings de ALSA en WSL/entornos sin audio
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings('ignore', category=UserWarning)


class AudioCapture:
    """Clase para capturar audio del sistema y micrófono."""
    
    # Formatos de audio comunes
    FORMAT = pyaudio.paInt16
    CHANNELS_MONO = 1
    CHANNELS_STEREO = 2
    DEFAULT_SAMPLE_RATE = 44100
    
    def __init__(self, sample_rate: int = DEFAULT_SAMPLE_RATE, 
                 channels: int = CHANNELS_STEREO):
        """
        Inicializar capturador de audio.
        
        Args:
            sample_rate: Tasa de muestreo (Hz).
            channels: Número de canales (1=mono, 2=stereo).
        """
        self.logger = get_logger("AudioCapture")
        self.sample_rate = sample_rate
        self.channels = channels
        # Suprimir stderr de ALSA durante inicialización
        old_stderr = sys.stderr
        try:
            sys.stderr = open(os.devnull, 'w')
            self.audio = pyaudio.PyAudio()
        except Exception:
            sys.stderr = old_stderr
            raise
        finally:
            sys.stderr = old_stderr
        self.stream = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.capture_thread = None
        self.frames_captured = []
        self.has_devices = False
        
    def get_audio_devices(self) -> List[Dict]:
        """
        Obtener lista de dispositivos de audio disponibles.
        
        Returns:
            Lista de diccionarios con información de dispositivos.
        """
        self.logger.debug("Buscando dispositivos de audio...")
        devices = []
        # Suprimir stderr de ALSA durante la enumeración
        old_stderr = sys.stderr
        try:
            sys.stderr = open(os.devnull, 'w')
            device_count = self.audio.get_device_count()
            
            for i in range(device_count):
                try:
                    info = self.audio.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:  # Solo dispositivos de entrada
                        self.logger.debug(f"  Dispositivo encontrado: {info['name']} (índice {i})")
                        devices.append({
                            'index': i,
                            'name': info['name'],
                            'channels': info['maxInputChannels'],
                            'sample_rate': int(info['defaultSampleRate'])
                        })
                except Exception:
                    continue
        finally:
            sys.stderr = old_stderr
        
        self.logger.debug(f"Encontrados {len(devices)} dispositivos de entrada.")
        self.has_devices = len(devices) > 0
        return devices
    
    def find_device_by_name(self, name: str) -> Optional[Dict]:
        """
        Buscar dispositivo por nombre.
        
        Args:
            name: Nombre del dispositivo.
            
        Returns:
            Diccionario con información del dispositivo o None.
        """
        devices = self.get_audio_devices()
        for device in devices:
            if name.lower() in device['name'].lower():
                return device
        return None
    
    def get_default_input_device(self) -> Dict:
        """
        Obtener dispositivo de entrada por defecto.
        
        Returns:
            Diccionario con información del dispositivo.
        """
        self.logger.debug("Buscando dispositivo de entrada por defecto...")
        try:
            default_index = self.audio.get_default_input_device_info()['index']
            info = self.audio.get_device_info_by_index(default_index)
            self.logger.debug(f"Dispositivo de entrada por defecto encontrado: {info['name']} (índice {default_index})")
            return {
                'index': default_index,
                'name': info['name'],
                'channels': info['maxInputChannels'],
                'sample_rate': int(info['defaultSampleRate'])
            }
        except Exception:
            # Si no hay dispositivo por defecto, usar el primero disponible
            devices = self.get_audio_devices()
            if devices:
                return devices[0]
            raise RuntimeError("No se encontraron dispositivos de audio de entrada")
    
    def start_capture(self, device_index: Optional[int] = None, 
                     callback: Optional[Callable] = None):
        """
        Iniciar captura de audio.
        
        Args:
            device_index: Índice del dispositivo. None = dispositivo por defecto.
            callback: Función callback para procesar audio en tiempo real.
            
        Raises:
            RuntimeError: Si no hay dispositivos de audio disponibles.
        """
        if self.is_recording:
            return
        
        # Verificar que hay dispositivos disponibles
        devices = self.get_audio_devices()
        if not devices:
            raise RuntimeError("No se encontraron dispositivos de audio de entrada")
        
        if device_index is None:
            try:
                device = self.get_default_input_device()
                device_index = device['index']
            except RuntimeError:
                # Si no hay dispositivo por defecto, usar el primero disponible
                if devices:
                    device_index = devices[0]['index']
                else:
                    raise RuntimeError("No se encontraron dispositivos de audio de entrada")
        
        self.logger.info(f"Iniciando captura de audio en dispositivo: {device_index}")
        self.logger.debug(f"Configuración: {self.sample_rate}Hz, {self.channels} canales")
        chunk_size = 1024
        
        # Suprimir stderr durante la apertura del stream
        old_stderr = sys.stderr
        try:
            sys.stderr = open(os.devnull, 'w')
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=chunk_size
            )
        except Exception as e:
            sys.stderr = old_stderr
            raise RuntimeError(f"No se pudo abrir el dispositivo de audio: {e}")
        finally:
            sys.stderr = old_stderr
        
        self.is_recording = True
        self.frames_captured = []
        
        if callback:
            self.capture_thread = threading.Thread(
                target=self._capture_with_callback,
                args=(callback,),
                daemon=True
            )
        else:
            self.capture_thread = threading.Thread(
                target=self._capture_to_queue,
                daemon=True
            )
        
        self.capture_thread.start()
    
    def _capture_with_callback(self, callback: Callable):
        """Capturar audio y llamar callback."""
        try:
            while self.is_recording:
                data = self.stream.read(1024, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                callback(audio_data)
        except Exception as e:
            self.logger.error(f"Error en captura de audio: {e}")
    
    def _capture_to_queue(self):
        """Capturar audio y almacenar en cola."""
        try:
            while self.is_recording:
                data = self.stream.read(1024, exception_on_overflow=False)
                self.audio_queue.put(data)
                self.frames_captured.append(data)
        except Exception as e:
            self.logger.error(f"Error en captura de audio: {e}")
    
    def get_audio_data(self, timeout: float = 0.1) -> Optional[bytes]:
        """
        Obtener datos de audio de la cola.
        
        Args:
            timeout: Tiempo de espera en segundos.
            
        Returns:
            Datos de audio o None si no hay datos.
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_all_captured_frames(self) -> bytes:
        """
        Obtener todos los frames capturados.
        
        Returns:
            Bytes con todos los frames de audio.
        """
        return b''.join(self.frames_captured)
    
    def stop_capture(self):
        """Detener captura de audio."""
        self.is_recording = False
        
        if self.capture_thread:
            self.logger.debug("Esperando a que el hilo de captura de audio termine...")
            self.capture_thread.join(timeout=2.0)
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def get_captured_size_mb(self) -> float:
        """
        Obtener tamaño de audio capturado en MB.
        
        Returns:
            Tamaño en megabytes.
        """
        total_bytes = sum(len(frame) for frame in self.frames_captured)
        return total_bytes / (1024 * 1024)
    
    def close(self):
        """Cerrar recursos de audio."""
        self.stop_capture()
        if self.audio:
            self.logger.debug("Terminando instancia de PyAudio.")
            self.audio.terminate()
            self.audio = None

