"""Módulo para codificación de video usando FFmpeg."""

import subprocess
import os
import threading
from typing import Optional
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

    def encode_from_raw_files(
        self,
        video_file: str,
        audio_file: Optional[str] = None,
        audio_sample_rate: int = 44100,
        audio_channels: int = 2,
    ) -> str:
        """
        Codificar video y audio desde archivos raw.

        Args:
            video_file: Ruta al archivo de video raw.
            audio_file: Ruta al archivo de audio raw (opcional).
            audio_sample_rate: Tasa de muestreo del audio.
            audio_channels: Canales de audio.

        Returns:
            Ruta del archivo final.
        """
        if not self.check_ffmpeg():
            raise RuntimeError("FFmpeg no está disponible")

        quality_settings = self.QUALITY_PRESETS[self.quality]

        cmd = [
            "ffmpeg",
            "-y",
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
            video_file,
        ]

        has_audio = (
            audio_file
            and os.path.exists(audio_file)
            and os.path.getsize(audio_file) > 0
        )

        if has_audio:
            cmd.extend(
                [
                    "-f",
                    "s16le",
                    "-ar",
                    str(audio_sample_rate),
                    "-ac",
                    str(audio_channels),
                    "-i",
                    audio_file,
                ]
            )

        # Configuración de salida
        if has_audio:
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
                    "-shortest",
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

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            raise RuntimeError(f"Error en codificación FFmpeg: {result.stderr}")

        if os.path.exists(self.output_path):
            return self.output_path
        else:
            raise RuntimeError(f"El archivo de salida no se generó: {self.output_path}")
