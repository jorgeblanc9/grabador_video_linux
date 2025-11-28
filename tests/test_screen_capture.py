"""Tests para captura de pantalla."""

import pytest
from src.core.screen_capture import ScreenCapture


def test_screen_capture_initialization():
    """Test de inicialización del capturador."""
    capture = ScreenCapture()
    assert capture is not None
    assert capture.monitors is not None
    assert len(capture.monitors) > 0
    capture.close()


def test_get_monitors():
    """Test de obtención de monitores."""
    capture = ScreenCapture()
    monitors = capture.get_monitors()
    assert isinstance(monitors, list)
    assert len(monitors) > 0
    capture.close()


def test_get_screen_size():
    """Test de obtención de tamaño de pantalla."""
    capture = ScreenCapture()
    width, height = capture.get_screen_size()
    assert width > 0
    assert height > 0
    capture.close()


def test_capture_full_screen():
    """Test de captura de pantalla completa."""
    capture = ScreenCapture()
    try:
        frame = capture.capture_full_screen()
        assert frame is not None
        assert len(frame.shape) == 3  # Debe ser imagen RGB/BGR
        assert frame.shape[2] == 3  # 3 canales
    except Exception as e:
        # En entornos sin display (WSL, CI), puede fallar
        # Esto es aceptable para el test
        import mss
        if isinstance(e, mss.exception.ScreenShotError):
            pytest.skip("No se puede capturar pantalla (sin display)")
        raise
    finally:
        capture.close()

