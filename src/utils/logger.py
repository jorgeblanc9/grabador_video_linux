"""Sistema de logging estructurado."""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(name: str = "grabador_video", 
                log_file: Optional[str] = None,
                level: int = logging.INFO) -> logging.Logger:
    """
    Configurar logger.
    
    Args:
        name: Nombre del logger.
        log_file: Archivo de log (opcional).
        level: Nivel de logging.
        
    Returns:
        Logger configurado.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Si ya tiene handlers, solo actualizamos el nivel
    if logger.handlers:
        for handler in logger.handlers:
            handler.setLevel(level)
        return logger
    
    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo si se especifica
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "grabador_video") -> logging.Logger:
    """
    Obtener logger existente o crear uno nuevo.
    
    Args:
        name: Nombre del logger.
        
    Returns:
        Logger.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        setup_logger(name)
    return logger

