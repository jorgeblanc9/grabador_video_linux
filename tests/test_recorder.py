"""Tests para el grabador de video."""

import pytest
import time
from src.core.recorder_manager import VideoRecorder


def test_recorder_initialization():
    """Test de inicialización del grabador."""
    recorder = VideoRecorder()
    assert recorder is not None
    assert recorder.fps == 30
    assert not recorder.is_recording
    recorder.cleanup()


def test_set_screen_region():
    """Test de configuración de región."""
    recorder = VideoRecorder()
    region = (100, 100, 800, 600)
    recorder.set_screen_region(region)
    assert recorder.region == region
    recorder.cleanup()


def test_get_elapsed_time():
    """Test de obtención de tiempo transcurrido."""
    recorder = VideoRecorder()
    elapsed = recorder.get_elapsed_time()
    assert elapsed == 0.0
    recorder.cleanup()

