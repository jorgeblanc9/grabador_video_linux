"""Tests de integración."""

import pytest
import os
from pathlib import Path
from src.core.unified_recorder import UnifiedRecorder


def test_unified_recorder_initialization():
    """Test de inicialización del grabador unificado."""
    recorder = UnifiedRecorder()
    assert recorder is not None
    recorder.cleanup()


def test_get_screen_resolution():
    """Test de obtención de resolución de pantalla."""
    recorder = UnifiedRecorder()
    width, height = recorder.get_screen_resolution()
    assert width > 0
    assert height > 0
    recorder.cleanup()


def test_get_system_info():
    """Test de obtención de información del sistema."""
    recorder = UnifiedRecorder()
    info = recorder.get_system_info()
    assert 'platform' in info
    assert 'python_version' in info
    assert 'monitors' in info
    recorder.cleanup()


def test_create_recorder():
    """Test de creación de grabador."""
    unified = UnifiedRecorder()
    recorder = unified.create_recorder(fps=30)
    assert recorder is not None
    assert recorder.fps == 30
    recorder.cleanup()
    unified.cleanup()

