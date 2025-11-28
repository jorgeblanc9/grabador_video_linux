"""Sistema de notificaciones de sonido para Linux."""

import subprocess
import platform
from pathlib import Path
from typing import Optional


def play_sound(sound_type: str = "default"):
    """
    Reproducir sonido de notificación.
    
    Args:
        sound_type: Tipo de sonido (success, error, warning, default).
    """
    # Intentar diferentes métodos en orden de preferencia
    methods = [
        _play_with_paplay,
        _play_with_aplay,
        _play_with_ffplay,
        _play_with_python_winsound
    ]
    
    for method in methods:
        try:
            if method(sound_type):
                return
        except Exception:
            continue
    
    # Si todos fallan, no hacer nada (silencioso)


def _play_with_paplay(sound_type: str) -> bool:
    """Reproducir con paplay (PulseAudio)."""
    try:
        # Usar sonido del sistema
        sound_file = _get_system_sound(sound_type)
        if sound_file and Path(sound_file).exists():
            subprocess.run(['paplay', sound_file], 
                         capture_output=True, 
                         check=True,
                         timeout=2)
            return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False


def _play_with_aplay(sound_type: str) -> bool:
    """Reproducir con aplay (ALSA)."""
    try:
        sound_file = _get_system_sound(sound_type)
        if sound_file and Path(sound_file).exists():
            subprocess.run(['aplay', sound_file], 
                         capture_output=True, 
                         check=True,
                         timeout=2)
            return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False


def _play_with_ffplay(sound_type: str) -> bool:
    """Reproducir con ffplay (FFmpeg)."""
    try:
        sound_file = _get_system_sound(sound_type)
        if sound_file and Path(sound_file).exists():
            subprocess.run(['ffplay', '-nodisp', '-autoexit', sound_file], 
                         capture_output=True, 
                         check=True,
                         timeout=2)
            return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False


def _play_with_python_winsound(sound_type: str) -> bool:
    """Reproducir con winsound (solo Windows, pero intentar en Linux)."""
    try:
        import winsound
        # En Linux esto probablemente falle, pero lo intentamos
        winsound.MessageBeep()
        return True
    except (ImportError, AttributeError):
        pass
    return False


def _get_system_sound(sound_type: str) -> Optional[str]:
    """
    Obtener ruta del sonido del sistema.
    
    Args:
        sound_type: Tipo de sonido.
        
    Returns:
        Ruta del archivo de sonido o None.
    """
    # Rutas comunes de sonidos del sistema en Linux
    sound_paths = [
        Path('/usr/share/sounds'),
        Path('/usr/share/sounds/freedesktop/stereo'),
        Path.home() / '.local/share/sounds',
    ]
    
    # Mapeo de tipos de sonido
    sound_files = {
        'success': ['complete.oga', 'bell.oga', 'dialog-information.oga'],
        'error': ['dialog-error.oga', 'bell.oga', 'dialog-warning.oga'],
        'warning': ['dialog-warning.oga', 'bell.oga'],
        'default': ['bell.oga', 'message.oga']
    }
    
    files_to_try = sound_files.get(sound_type, sound_files['default'])
    
    for sound_path in sound_paths:
        for sound_file in files_to_try:
            full_path = sound_path / sound_file
            if full_path.exists():
                return str(full_path)
    
    return None


def notify_success():
    """Notificación de éxito."""
    play_sound("success")


def notify_error():
    """Notificación de error."""
    play_sound("error")


def notify_warning():
    """Notificación de advertencia."""
    play_sound("warning")

