"""Módulo para codificación de video usando FFmpeg."""

import subprocess
import os
import threading
from typing import Optional, Dict
from pathlib import Path


class VideoEncoder:
    """Clase para codificar video usando FFmpeg."""

    # Configuraciones de calidad
    QUALITY_PRESETS = {
        "Alta": {"video_bitrate": "5000k", "audio_bitrate": "192k", "crf": "18"},
        "Media": {"video_bitrate": "3000k", "audio_bitrate": "128k", "crf": "23"},
        "Baja": {"video_bitrate": "1000k", "audio_bitrate": "96k", "crf": "28"},
    }

    # Formatos soportados
    SUPPORTED_FORMATS = ["mp4", "avi", "mov", "mkv"]

    def __init__(
        self,
        output_path: str,
        width: int,
        height: int,
        fps: int = 30,
        format: str = "mp4",
        quality: str = "Alta",
    ):
        """
        Inicializar codificador de video.

        Args:
            output_path: Ruta del archivo de salida.
            width: Ancho del video.
            height: Alto del video.
            fps: Frames por segundo.
            format: Formato de salida (mp4, avi, mov, mkv).
            quality: Calidad (Alta, Media, Baja).
        """
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.format = format.lower()
        self.quality = quality

        if self.format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Formato no soportado: {format}")

        if quality not in self.QUALITY_PRESETS:
            raise ValueError(f"Calidad no válida: {quality}")

        # Asegurar extensión correcta
        output_path_obj = Path(output_path)
        if output_path_obj.suffix.lower() != f".{self.format}":
            self.output_path = str(output_path_obj.with_suffix(f".{self.format}"))

        self.process = None
        self.encoding = False
        self.has_audio = False
        self.audio_sample_rate = 44100
        self.audio_channels = 2

    def check_ffmpeg(self) -> bool:
        """
        Verificar si FFmpeg está disponible.

        Returns:
            True si FFmpeg está disponible.
        """
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def start_encoding(
        self,
        video_input: str = "pipe:",
        audio_input: Optional[str] = None,
        has_audio: bool = False,
        audio_sample_rate: int = 44100,
        audio_channels: int = 2,
    ):
        """
        Iniciar codificación de video.

        Args:
            video_input: Fuente de video (pipe: para stdin, o archivo).
            audio_input: Fuente de audio (opcional, para archivos).
            has_audio: Si True, se espera audio en tiempo real.
            audio_sample_rate: Tasa de muestreo de audio (si has_audio=True).
            audio_channels: Canales de audio (si has_audio=True).
        """
        if not self.check_ffmpeg():
            raise RuntimeError("FFmpeg no está disponible. Instálalo con: make install")

        if self.encoding:
            return

        self.has_audio = has_audio
        if has_audio:
            self.audio_sample_rate = audio_sample_rate
            self.audio_channels = audio_channels

        quality_settings = self.QUALITY_PRESETS[self.quality]

        # Construir comando FFmpeg
        cmd = [
            "ffmpeg",
            "-y",  # Sobrescribir archivo si existe
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-s",
            f"{self.width}x{self.height}",
            "-pix_fmt",
            "bgr24",
            "-r",
            str(self.fps),
            "-i",
            video_input,
        ]

        # Agregar audio si está disponible (archivo)
        if audio_input:
            cmd.extend(
                [
                    "-f",
                    "s16le",
                    "-ar",
                    "44100",
                    "-ac",
                    "2",
                    "-i",
                    audio_input,
                ]
            )
        elif has_audio:
            # Audio en tiempo real - usar pipe separado
            cmd.extend(
                [
                    "-f",
                    "s16le",
                    "-ar",
                    str(audio_sample_rate),
                    "-ac",
                    str(audio_channels),
                    "-i",
                    "pipe:1",  # Segundo pipe para audio
                ]
            )

        # Configuración de salida
        if has_audio or audio_input:
            cmd.extend(
                [
                    "-c:v",
                    "libx264",
                    "-preset",
                    "medium",
                    "-crf",
                    quality_settings["crf"],
                    "-c:a",
                    "aac" if self.format == "mp4" else "libmp3lame",
                    "-b:a",
                    quality_settings["audio_bitrate"],
                    "-pix_fmt",
                    "yuv420p",
                    "-shortest",  # Terminar cuando el stream más corto termine
                    self.output_path,
                ]
            )
        else:
            cmd.extend(
                [
                    "-c:v",
                    "libx264",
                    "-preset",
                    "medium",
                    "-crf",
                    quality_settings["crf"],
                    "-pix_fmt",
                    "yuv420p",
                    self.output_path,
                ]
            )

        if has_audio:
            # Crear dos pipes: uno para video (stdin) y otro para audio
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,  # Video
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Para audio en tiempo real, necesitamos usar un enfoque diferente
            # Usaremos un archivo temporal o named pipe
            import tempfile

            self.audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".raw")
            self.audio_file_path = self.audio_file.name
            self.audio_file.close()
        else:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.audio_file_path = None

        self.encoding = True

    def write_frame(self, frame: bytes):
        """
        Escribir frame al proceso de codificación.

        Args:
            frame: Datos del frame en formato BGR.
        """
        if self.process and self.process.stdin and not self.process.stdin.closed:
            try:
                self.process.stdin.write(frame)
                self.process.stdin.flush()
            except (BrokenPipeError, ValueError, OSError):
                # El proceso terminó o stdin está cerrado
                self.encoding = False

    def write_audio(self, audio_data: bytes):
        """
        Escribir datos de audio al proceso de codificación.

        Args:
            audio_data: Datos de audio en formato s16le.
        """
        if not self.has_audio:
            return

        # Si hay audio en tiempo real, guardarlo en archivo temporal
        # y mezclarlo al final
        if self.audio_file_path:
            try:
                with open(self.audio_file_path, "ab") as f:
                    f.write(audio_data)
            except Exception as e:
                # Ignorar errores de escritura de audio
                pass

    def finish_encoding(self) -> str:
        """
        Finalizar codificación y cerrar proceso.

        Returns:
            Ruta del archivo generado.
        """
        if self.process:
            # Cerrar stdin de forma segura
            if self.process.stdin and not self.process.stdin.closed:
                try:
                    self.process.stdin.close()
                except (ValueError, OSError):
                    # stdin ya estaba cerrado o el proceso terminó
                    pass

            # Esperar a que termine el proceso
            try:
                stdout, stderr = self.process.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                # Si el proceso no termina, forzar terminación
                self.process.kill()
                stdout, stderr = self.process.communicate()
            except ValueError:
                # El proceso ya terminó
                stdout, stderr = b"", b""

            if self.process.returncode and self.process.returncode != 0:
                error_msg = (
                    stderr.decode("utf-8", errors="ignore")
                    if stderr
                    else "Error desconocido"
                )
                # No lanzar error si el archivo se generó correctamente
                if not os.path.exists(self.output_path):
                    raise RuntimeError(f"Error en codificación FFmpeg: {error_msg}")

            self.process = None
            self.encoding = False

        # Si hay audio en archivo temporal, mezclarlo con el video
        if (
            self.has_audio
            and self.audio_file_path
            and os.path.exists(self.audio_file_path)
        ):
            try:
                # Verificar que el archivo de audio no esté vacío
                if os.path.getsize(self.audio_file_path) > 0:
                    # Crear archivo temporal para video sin audio
                    temp_video = self.output_path + ".temp"
                    if os.path.exists(self.output_path):
                        os.rename(self.output_path, temp_video)

                    # Mezclar audio con video
                    quality_settings = self.QUALITY_PRESETS[self.quality]
                    cmd = [
                        "ffmpeg",
                        "-y",
                        "-i",
                        temp_video,
                        "-f",
                        "s16le",
                        "-ar",
                        str(self.audio_sample_rate),
                        "-ac",
                        str(self.audio_channels),
                        "-i",
                        self.audio_file_path,
                        "-c:v",
                        "copy",  # Copiar video sin re-encodificar
                        "-c:a",
                        "aac" if self.format == "mp4" else "libmp3lame",
                        "-b:a",
                        quality_settings["audio_bitrate"],
                        "-shortest",
                        self.output_path,
                    ]

                    result = subprocess.run(cmd, capture_output=True, timeout=60)
                    if result.returncode == 0:
                        # Eliminar archivos temporales
                        if os.path.exists(temp_video):
                            os.remove(temp_video)
                    else:
                        # Si falla la mezcla, restaurar video original
                        if os.path.exists(temp_video):
                            os.rename(temp_video, self.output_path)

                # Eliminar archivo de audio temporal
                if os.path.exists(self.audio_file_path):
                    os.remove(self.audio_file_path)
            except Exception as e:
                # Si hay error al mezclar audio, continuar con video sin audio
                if os.path.exists(self.audio_file_path):
                    try:
                        os.remove(self.audio_file_path)
                    except:
                        pass

        if os.path.exists(self.output_path):
            return self.output_path
        else:
            raise RuntimeError(f"El archivo de salida no se generó: {self.output_path}")

    def encode_from_files(
        self, video_file: str, audio_file: Optional[str] = None
    ) -> str:
        """
        Codificar video desde archivos existentes.

        Args:
            video_file: Archivo de video.
            audio_file: Archivo de audio (opcional).

        Returns:
            Ruta del archivo generado.
        """
        if not self.check_ffmpeg():
            raise RuntimeError("FFmpeg no está disponible")

        quality_settings = self.QUALITY_PRESETS[self.quality]

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_file,
        ]

        if audio_file:
            cmd.extend(["-i", audio_file])

        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                quality_settings["crf"],
                "-c:a",
                "aac" if self.format == "mp4" else "libmp3lame",
                "-b:a",
                quality_settings["audio_bitrate"],
                self.output_path,
            ]
        )

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"Error en codificación: {result.stderr}")

        return self.output_path
