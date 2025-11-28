"""Gestión de nombres de archivo y rutas."""

from pathlib import Path
from datetime import datetime
from typing import Optional


def generate_output_filename(prefix: str = "grabacion", 
                           extension: str = "mp4",
                           directory: Optional[str] = None) -> str:
    """
    Generar nombre de archivo único con timestamp.
    
    Args:
        prefix: Prefijo del nombre.
        extension: Extensión del archivo.
        directory: Directorio de salida (opcional).
        
    Returns:
        Ruta completa del archivo.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.{extension}"
    
    if directory:
        output_dir = Path(directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        return str(output_dir / filename)
    
    return filename


def ensure_directory(path: str) -> Path:
    """
    Asegurar que el directorio existe.
    
    Args:
        path: Ruta del archivo o directorio.
        
    Returns:
        Path del directorio.
    """
    file_path = Path(path)
    if file_path.suffix:  # Es un archivo
        file_path.parent.mkdir(parents=True, exist_ok=True)
        return file_path.parent
    else:  # Es un directorio
        file_path.mkdir(parents=True, exist_ok=True)
        return file_path


def get_file_size_mb(filepath: str) -> float:
    """
    Obtener tamaño de archivo en MB.
    
    Args:
        filepath: Ruta del archivo.
        
    Returns:
        Tamaño en megabytes.
    """
    file_path = Path(filepath)
    if file_path.exists():
        return file_path.stat().st_size / (1024 * 1024)
    return 0.0


def validate_output_path(filepath: str) -> bool:
    """
    Validar que la ruta de salida sea válida.
    
    Args:
        filepath: Ruta del archivo.
        
    Returns:
        True si es válida.
    """
    try:
        path = Path(filepath)
        # Verificar que el directorio padre sea escribible
        if path.parent.exists():
            return path.parent.is_dir() and path.parent.stat().st_mode & 0o200
        # Si no existe, verificar que el directorio actual sea escribible
        return Path.cwd().stat().st_mode & 0o200
    except Exception:
        return False

