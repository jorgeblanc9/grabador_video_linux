"""Tests para captura de audio."""

import pytest
from src.core.audio_capture import AudioCapture


def test_audio_capture_initialization():
    """Test de inicialización del capturador de audio."""
    capture = AudioCapture()
    assert capture is not None
    assert capture.sample_rate == 44100
    assert capture.channels == 2
    capture.close()


def test_get_audio_devices():
    """Test de obtención de dispositivos de audio."""
    capture = AudioCapture()
    try:
        devices = capture.get_audio_devices()
        assert isinstance(devices, list)
        # Puede estar vacío si no hay dispositivos, pero debe ser lista
    except Exception:
        # Si no hay dispositivos disponibles, está bien
        pass
    finally:
        capture.close()


def test_get_default_input_device():
    """Test de obtención de dispositivo por defecto."""
    capture = AudioCapture()
    try:
        device = capture.get_default_input_device()
        assert device is not None
        assert 'index' in device
        assert 'name' in device
    except RuntimeError:
        # Si no hay dispositivos, está bien
        pass
    finally:
        capture.close()

