"""Gestor principal de grabación de video."""

import threading
import time
from typing import Optional, Tuple, Callable
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

        self.frame_buffer = FrameBuffer(max_size=100)
        self.audio_buffer = AudioBuffer(max_size=200)
        self.sync_manager = SyncManager(self.frame_buffer, self.audio_buffer)

        self.is_recording = False
        self.is_paused = False
        self.recording_thread = None
        self.encoding_thread = None
        self.audio_encoding_thread = None

        self.duration = None
        self.start_time = None
        self.paused_time = 0.0
        self.pause_start = None

        self.progress_callback: Optional[Callable] = None
        self.frames_captured = 0

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

        # Obtener dimensiones
        if self.region:
            width, height = self.region[2], self.region[3]
        else:
            width, height = self.screen_capture.get_screen_size(self.monitor_index)

        self.logger.debug(f"Dimensiones del video: {width}x{height}")

        # Inicializar codificador
        self.video_encoder = VideoEncoder(
            output_path=output_path,
            width=width,
            height=height,
            fps=self.fps,
            format=format,
            quality=quality,
        )

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
                # Verificar que hay dispositivos antes de iniciar
                devices = self.audio_capture.get_audio_devices()
                if not devices:
                    self.logger.warning(
                        "Audio habilitado pero no hay dispositivos disponibles. Continuando sin audio."
                    )
                    self.audio_capture = None
                else:
                    # El audio se iniciará después de establecer start_time
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

        # Iniciar codificación
        self.logger.debug("Iniciando codificador de video...")
        has_audio = self.audio_capture is not None
        audio_sample_rate_val = sample_rate if has_audio else 44100
        audio_channels_val = audio_channels if has_audio else 2
        self.video_encoder.start_encoding(
            has_audio=has_audio,
            audio_sample_rate=audio_sample_rate_val,
            audio_channels=audio_channels_val,
        )

        self.is_recording = True
        self.is_paused = False
        self.duration = duration
        self.start_time = time.time()
        self.paused_time = 0.0
        self.frames_captured = 0

        # Iniciar captura de audio con callback si está habilitada
        if self.audio_capture and hasattr(self, "_audio_device_index"):

            def audio_callback(audio_data):
                """Callback para capturar audio y agregarlo al buffer."""
                if self.is_recording and not self.is_paused:
                    elapsed = time.time() - self.start_time - self.paused_time
                    self.audio_buffer.put(audio_data.tobytes(), elapsed)

            # Iniciar captura con callback
            if self.audio_capture.is_recording:
                self.audio_capture.stop_capture()
            self.audio_capture.start_capture(
                device_index=self._audio_device_index, callback=audio_callback
            )

        # Iniciar hilos
        self.recording_thread = threading.Thread(
            target=self._recording_loop, daemon=True
        )
        self.encoding_thread = threading.Thread(target=self._encoding_loop, daemon=True)

        # Hilo para procesar audio si está habilitado
        if self.audio_capture:
            self.audio_encoding_thread = threading.Thread(
                target=self._audio_encoding_loop, daemon=True
            )

        self.sync_manager.start()
        self.recording_thread.start()
        self.encoding_thread.start()
        if self.audio_encoding_thread:
            self.audio_encoding_thread.start()
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

                    frame_bytes = frame.tobytes()
                    self.frame_buffer.put(frame_bytes, elapsed)
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
        while self.is_recording or self.frame_buffer.size() > 0:
            frame_data = self.frame_buffer.get(timeout=0.1)
            if frame_data:
                frame, _ = frame_data
                self.video_encoder.write_frame(frame)

    def _audio_encoding_loop(self):
        """Loop de codificación de audio."""
        while self.is_recording or self.audio_buffer.size() > 0:
            if self.is_paused:
                time.sleep(0.1)
                continue

            audio_data = self.audio_buffer.get(timeout=0.1)
            if audio_data:
                audio_bytes, _ = audio_data
                # El audio ya viene en formato s16le desde PyAudio
                self.video_encoder.write_audio(audio_bytes)

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

        # Esperar a que terminen los hilos
        if self.recording_thread:
            self.logger.debug("Esperando al hilo de grabación...")
            self.recording_thread.join(timeout=5.0)

        if self.encoding_thread:
            self.logger.debug("Esperando al hilo de codificación...")
            self.encoding_thread.join(timeout=5.0)

        if self.audio_encoding_thread:
            self.logger.debug("Esperando al hilo de codificación de audio...")
            self.audio_encoding_thread.join(timeout=5.0)

        # Detener captura de audio
        if self.audio_capture:
            self.audio_capture.stop_capture()

        # Finalizar codificación
        if self.video_encoder:
            self.logger.debug("Finalizando codificación del video...")
            output_file = self.video_encoder.finish_encoding()
            self.logger.info(f"Archivo de video generado: {output_file}")
            return output_file

        self.logger.warning(
            "El codificador no estaba disponible al detener la grabación."
        )
        return None

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
