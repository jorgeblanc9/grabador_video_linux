"""Interfaz de línea de comandos para el grabador."""

import argparse
import sys
import time
from pathlib import Path
from typing import List

from ..core.unified_recorder import UnifiedRecorder
from ..utils.file_manager import generate_output_filename, validate_output_path
from ..utils.logger import get_logger
from ..utils.notifications import notify_success, notify_error


def main(argv: List[str] = None):
    """Función principal de la CLI."""
    parser = argparse.ArgumentParser(
        description="Grabador de Video y Audio - Interfaz de Línea de Comandos",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Argumentos de grabación
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Duración de la grabación en segundos (default: 60)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Archivo de salida (default: auto-generado)'
    )
    
    parser.add_argument(
        '--fps',
        type=int,
        default=30,
        help='Frames por segundo (default: 30)'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['mp4', 'avi', 'mov', 'mkv'],
        default='mp4',
        help='Formato de salida (default: mp4)'
    )
    
    parser.add_argument(
        '--quality',
        type=str,
        choices=['Alta', 'Media', 'Baja'],
        default='Alta',
        help='Calidad del video (default: Alta)'
    )
    
    # Argumentos de audio
    parser.add_argument(
        '--audio',
        action='store_true',
        help='Habilitar captura de audio'
    )
    
    parser.add_argument(
        '--audio-device',
        type=int,
        default=None,
        help='Índice del dispositivo de audio'
    )
    
    parser.add_argument(
        '--sample-rate',
        type=int,
        default=44100,
        choices=[44100, 48000, 96000],
        help='Tasa de muestreo de audio (default: 44100)'
    )
    
    parser.add_argument(
        '--channels',
        type=int,
        choices=[1, 2],
        default=2,
        help='Canales de audio: 1=mono, 2=stereo (default: 2)'
    )
    
    # Argumentos de región
    parser.add_argument(
        '--region',
        type=str,
        default=None,
        help='Región de captura: x,y,width,height (ej: 0,0,1920,1080)'
    )
    
    # Argumentos de monitor
    parser.add_argument(
        '--monitor',
        type=int,
        default=1,
        help='Índice del monitor a capturar (default: 1)'
    )
    
    args = parser.parse_args(argv)
    
    # Obtener logger (ya configurado en src/main.py)
    logger = get_logger()
    
    # Generar nombre de archivo si no se especifica
    output_file = args.output
    if not output_file:
        output_file = generate_output_filename(extension=args.format)
    else:
        # Normalizar ruta para que siempre esté en captures
        captures_dir = Path("captures")
        captures_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = Path(output_file)
        # Si es una ruta absoluta fuera de captures, extraer solo el nombre
        if file_path.is_absolute() and str(captures_dir.absolute()) not in str(file_path.absolute()):
            output_file = str(captures_dir / file_path.name)
            logger.debug(f"Ruta normalizada a: {output_file}")
        # Si es una ruta relativa, asegurar que esté en captures
        elif not file_path.is_absolute():
            output_file = str(captures_dir / file_path.name)
            logger.debug(f"Ruta normalizada a: {output_file}")
    
    # Validar ruta de salida
    if not validate_output_path(output_file):
        logger.error(f"La ruta de salida no es válida: {output_file}")
        sys.exit(1)
    
    # Parsear región si se especifica
    region = None
    if args.region:
        try:
            coords = [int(x.strip()) for x in args.region.split(',')]
            if len(coords) == 4:
                region = tuple(coords)
            else:
                logger.error("La región debe tener formato: x,y,width,height")
                sys.exit(1)
        except ValueError:
            logger.error("Error al parsear región. Use formato: x,y,width,height")
            sys.exit(1)
    
    # Crear grabador
    unified_recorder = UnifiedRecorder()
    recorder = unified_recorder.create_recorder(fps=args.fps)
    
    try:
        # Configurar región
        if region:
            recorder.set_screen_region(region)
        else:
            recorder.set_monitor(args.monitor)
        
        # Callback de progreso
        def progress_callback(elapsed, remaining, frames, audio_mb):
            if remaining is not None:
                progress = (elapsed / (elapsed + remaining)) * 100
                logger.info(
                    f"Progreso: {progress:.1f}% | "
                    f"Tiempo: {elapsed:.1f}s / {elapsed + remaining:.1f}s | "
                    f"Frames: {frames} | Audio: {audio_mb:.2f} MB"
                )
            else:
                logger.info(
                    f"Grabando... | Tiempo: {elapsed:.1f}s | "
                    f"Frames: {frames} | Audio: {audio_mb:.2f} MB"
                )
        
        recorder.set_progress_callback(progress_callback)
        
        # Iniciar grabación
        logger.info(f"Iniciando grabación: {output_file}")
        logger.info(f"Duración: {args.duration}s | FPS: {args.fps} | Formato: {args.format} | Calidad: {args.quality}")
        
        if args.audio:
            logger.info(f"Audio: Habilitado | Sample Rate: {args.sample_rate}Hz | Canales: {args.channels}")
        
        recorder.start_recording(
            duration=args.duration,
            output_path=output_file,
            format=args.format,
            quality=args.quality,
            enable_audio=args.audio,
            audio_device_index=args.audio_device,
            sample_rate=args.sample_rate,
            audio_channels=args.channels
        )
        
        # Esperar a que termine
        logger.info("Grabación en progreso... (Ctrl+C para cancelar)")
        
        try:
            while recorder.is_recording:
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.warning("Grabación cancelada por el usuario")
            recorder.stop_recording()
            sys.exit(1)
        
        # Finalizar
        output_path = recorder.stop_recording()
        
        if output_path and Path(output_path).exists():
            file_size = Path(output_path).stat().st_size / (1024 * 1024)
            logger.info(f"Grabación completada: {output_path} ({file_size:.2f} MB)")
            notify_success()
            sys.exit(0)
        else:
            logger.error("La grabación no se completó correctamente")
            notify_error()
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error durante la grabación: {e}", exc_info=logger.level == 10) # 10 is DEBUG level
        notify_error()
        sys.exit(1)
    finally:
        recorder.cleanup()
        unified_recorder.cleanup()


if __name__ == '__main__':
    main()

