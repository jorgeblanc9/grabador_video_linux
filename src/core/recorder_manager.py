"""Gestor principal de grabación de video."""

import threading
import time
from typing import Optional, Tuple, Callable
import tempfile
import os

from .screen_capture import ScreenCapture
from .audio_capture import AudioCapture
from .video_encoder import VideoEncoder
from .buffering import FrameBuffer, AudioBuffer
from .sync_manager import SyncManager
from ..utils.logger import get_logger


class VideoRecorder:
    """Gestor principal para grabación de video y audio."""

    def __init__(self, fps: int = 30):
        """
        Inicializar grabador de video.

        Args:
            fps: Frames por segundo.
        """
        self.logger = get_logger("VideoRecorder")
        self.fps = fps
        self.frame_time = 1.0 / fps

        self.screen_capture = ScreenCapture()
        self.audio_capture = None
        self.video_encoder = None

        # Buffers no se usarán para la nueva estrategia
        self.frame_buffer = None
        self.audio_buffer = None
        self.sync_manager = None

        self.is_recording = False
        self.is_paused = False
        self.recording_thread = None

        self.duration = None
        self.start_time = None
        self.paused_time = 0.0
        self.pause_start = None

        self.progress_callback: Optional[Callable] = None
        self.frames_captured = 0

        # Atributos para la grabación en archivos
        self.raw_video_file = None
        self.raw_audio_file = None
        self._output_path = None
        self._format = None
        self._quality = None
        self._width = 0
        self._height = 0
        self._sample_rate = 44100
        self._audio_channels = 2

        # Configuración de región
        self.region = None  # (x, y, width, height) o None para pantalla completa
        self.monitor_index = 1  # Monitor principal

    def set_screen_region(self, region: Optional[Tuple[int, int, int, int]]):
        """
        Establecer región de captura.

        Args:
            region: Tupla (x, y, width, height) o None para pantalla completa.
        """
        self.region = region

    def set_monitor(self, monitor_index: int):
        """
        Establecer monitor a capturar.

        Args:
            monitor_index: Índice del monitor (1 = primer monitor).
        """
        self.monitor_index = monitor_index

    def set_progress_callback(self, callback: Callable):
        """
        Establecer callback para progreso.

        Args:
            callback: Función que recibe (elapsed_time, remaining_time, frames, audio_mb).
        """
        self.progress_callback = callback

    def start_recording(
        self,
        duration: Optional[float] = None,
        output_path: str = "grabacion.mp4",
        format: str = "mp4",
        quality: str = "Alta",
        enable_audio: bool = False,
        audio_device_index: Optional[int] = None,
        sample_rate: int = 44100,
        audio_channels: int = 2,
    ):
        """
        Iniciar grabación.

        Args:
            duration: Duración en segundos (None = sin límite).
            output_path: Ruta del archivo de salida.
            format: Formato de salida (mp4, avi, mov, mkv).
            quality: Calidad (Alta, Media, Baja).
            enable_audio: Habilitar captura de audio.
            audio_device_index: Índice del dispositivo de audio.
            sample_rate: Tasa de muestreo de audio.
            audio_channels: Canales de audio (1=mono, 2=stereo).
        """
        self.logger.info("Solicitud para iniciar grabación...")
        if self.is_recording:
            self.logger.warning("La grabación ya está en progreso.")
            return

        # Guardar configuración para la codificación final
        self._output_path = output_path
        self._format = format
        self._quality = quality
        self._sample_rate = sample_rate
        self._audio_channels = audio_channels

        # Obtener dimensiones
        if self.region:
            self._width, self._height = self.region[2], self.region[3]
        else:
            self._width, self._height = self.screen_capture.get_screen_size(
                self.monitor_index
            )

        self.logger.debug(f"Dimensiones del video: {self._width}x{self._height}")

        # Crear archivos temporales para video y audio raw
        self.raw_video_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".rawvideo"
        )
        self.raw_audio_file = None

        # Inicializar captura de audio si está habilitada
        if enable_audio:
            self.logger.info("Captura de audio habilitada.")
            self.logger.debug(
                f"Dispositivo: {audio_device_index}, Sample Rate: {sample_rate}, Canales: {audio_channels}"
            )
            try:
                self.audio_capture = AudioCapture(
                    sample_rate=sample_rate, channels=audio_channels
                )
                devices = self.audio_capture.get_audio_devices()
                if not devices:
                    self.logger.warning(
                        "Audio habilitado pero no hay dispositivos disponibles. Continuando sin audio."
                    )
                    self.audio_capture = None
                else:
                    self.raw_audio_file = tempfile.NamedTemporaryFile(
                        delete=False, suffix=".rawaudio"
                    )
                    self._audio_device_index = audio_device_index
            except RuntimeError as e:
                self.logger.warning(
                    f"No se pudo inicializar captura de audio: {e}. Continuando sin audio."
                )
                self.audio_capture = None
            except Exception as e:
                self.logger.error(
                    f"Error inesperado al inicializar audio: {e}. Continuando sin audio."
                )
                self.audio_capture = None

        self.is_recording = True
        self.is_paused = False
        self.duration = duration
        self.start_time = time.time()
        self.paused_time = 0.0
        self.frames_captured = 0

        # Iniciar captura de audio si está habilitada
        if self.audio_capture and self.raw_audio_file:

            def audio_callback(audio_data):
                if self.is_recording and not self.is_paused:
                    try:
                        self.raw_audio_file.write(audio_data.tobytes())
                    except Exception as e:
                        self.logger.error(
                            f"Error escribiendo en archivo de audio raw: {e}"
                        )

            self.audio_capture.start_capture(
                device_index=self._audio_device_index, callback=audio_callback
            )

        # Iniciar hilo de grabación de video
        self.recording_thread = threading.Thread(
            target=self._recording_loop, daemon=True
        )
        self.recording_thread.start()
        self.logger.info("Grabación iniciada correctamente.")

    def _recording_loop(self):
        """Loop principal de grabación."""
        last_frame_time = time.time()

        while self.is_recording:
            if self.is_paused:
                if self.pause_start is None:
                    self.pause_start = time.time()
                time.sleep(0.1)
                continue

            # Reanudar desde pausa
            if self.pause_start is not None:
                self.paused_time += time.time() - self.pause_start
                self.pause_start = None

            current_time = time.time()
            elapsed = current_time - self.start_time - self.paused_time

            # Verificar duración
            if self.duration and elapsed >= self.duration:
                self.stop_recording()
                break

            # Capturar frame
            if current_time - last_frame_time >= self.frame_time:
                try:
                    if self.region:
                        frame = self.screen_capture.capture_region(
                            self.region[0],
                            self.region[1],
                            self.region[2],
                            self.region[3],
                            self.monitor_index,
                        )
                    else:
                        frame = self.screen_capture.capture_full_screen(
                            self.monitor_index
                        )

                    if self.raw_video_file:
                        self.raw_video_file.write(frame.tobytes())

                    self.frames_captured += 1
                    last_frame_time = current_time
                except Exception as e:
                    self.logger.error(f"Error capturando frame: {e}")

            # Actualizar progreso
            if self.progress_callback:
                remaining = (self.duration - elapsed) if self.duration else None
                audio_mb = (
                    self.audio_capture.get_captured_size_mb()
                    if self.audio_capture
                    else 0.0
                )
                self.progress_callback(
                    elapsed, remaining, self.frames_captured, audio_mb
                )

            time.sleep(0.001)  # Pequeña pausa para no saturar CPU

    def _encoding_loop(self):
        """Loop de codificación de video."""
        # Este método ya no es necesario
        pass

    def _audio_encoding_loop(self):
        """Loop de codificación de audio."""
        # Este método ya no es necesario
        pass

    def pause_recording(self):
        """Pausar grabación."""
        if self.is_recording and not self.is_paused:
            self.is_paused = True
            self.pause_start = time.time()

    def resume_recording(self):
        """Reanudar grabación."""
        if self.is_recording and self.is_paused:
            self.is_paused = False
            if self.pause_start:
                self.paused_time += time.time() - self.pause_start
                self.pause_start = None

    def stop_recording(self) -> str:
        """
        Detener grabación.

        Returns:
            Ruta del archivo generado.
        """
        if not self.is_recording:
            return None

        self.logger.info("Deteniendo grabación...")
        self.is_recording = False

        # Esperar a que terminen los hilos, excepto si nos llamamos a nosotros mismos
        if (
            self.recording_thread
            and threading.current_thread() != self.recording_thread
        ):
            self.logger.debug("Esperando al hilo de grabación...")
            self.recording_thread.join(timeout=5.0)

        # Detener captura de audio
        if self.audio_capture:
            self.audio_capture.stop_capture()

        # Cerrar archivos temporales
        if self.raw_video_file:
            self.raw_video_file.close()
        if self.raw_audio_file:
            self.raw_audio_file.close()

        # Finalizar codificación
        self.logger.info("Codificando el archivo de video final...")
        try:
            encoder = VideoEncoder(
                output_path=self._output_path,
                width=self._width,
                height=self._height,
                fps=self.fps,
                format=self._format,
                quality=self._quality,
            )

            audio_path = self.raw_audio_file.name if self.raw_audio_file else None

            output_file = encoder.encode_from_raw_files(
                video_file=self.raw_video_file.name,
                audio_file=audio_path,
                audio_sample_rate=self._sample_rate,
                audio_channels=self._audio_channels,
            )
            self.logger.info(f"Archivo de video generado: {output_file}")

            return output_file
        except Exception as e:
            self.logger.error(f"Error durante la codificación final: {e}")
            return None
        finally:
            # Limpiar archivos temporales
            if self.raw_video_file and os.path.exists(self.raw_video_file.name):
                os.remove(self.raw_video_file.name)
            if self.raw_audio_file and os.path.exists(self.raw_audio_file.name):
                os.remove(self.raw_audio_file.name)

    def get_elapsed_time(self) -> float:
        """
        Obtener tiempo transcurrido.

        Returns:
            Tiempo en segundos.
        """
        if not self.start_time:
            return 0.0

        if self.is_paused and self.pause_start:
            return (
                self.start_time
                - time.time()
                - self.paused_time
                - (time.time() - self.pause_start)
            )

        return time.time() - self.start_time - self.paused_time

    def get_remaining_time(self) -> Optional[float]:
        """
        Obtener tiempo restante.

        Returns:
            Tiempo en segundos o None si no hay duración límite.
        """
        if not self.duration:
            return None

        elapsed = self.get_elapsed_time()
        remaining = self.duration - elapsed
        return max(0.0, remaining)

    def cleanup(self):
        """Limpiar recursos."""
        self.stop_recording()

        if self.audio_capture:
            self.audio_capture.close()

        if self.screen_capture:
            self.screen_capture.close()
        self.logger.debug("Recursos del grabador limpiados.")
