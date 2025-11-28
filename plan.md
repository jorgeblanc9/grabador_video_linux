# Plan: Portar Grabador de Video a Linux

## Objetivo

Crear una versión del grabador de video completamente compatible con Linux desde cero, manteniendo toda la funcionalidad del programa original pero usando librerías y APIs multiplataforma.

## Análisis de Dependencias Windows-Specific

### Dependencias a Reemplazar:

1. **PIL ImageGrab** (`screen_capture.py`, `unified_recorder.py`): No funciona en Linux sin X11, lento
2. **ctypes.windll.user32** (`unified_recorder.py`): API específica de Windows para métricas de pantalla
3. **winsound** (`notifications.py`): Ya tiene fallback, pero necesita verificación en Linux

### Dependencias que Funcionan en Linux:

- `opencv-python`: Multiplataforma
- `pyaudio`: Funciona en Linux (requiere dependencias del sistema)
- `numpy`, `Pillow`: Multiplataforma
- `ffmpeg-python`: Multiplataforma
- `psutil`: Multiplataforma
- `tkinter`: Incluido en Python, funciona en Linux

## Estructura del Proyecto Linux

```
grabador_video_linux/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── screen_capture.py      # Usar mss en lugar de ImageGrab
│   │   ├── audio_capture.py       # Adaptar detección de dispositivos Linux
│   │   ├── video_encoder.py       # Sin cambios (FFmpeg)
│   │   ├── recorder_manager.py    # Adaptar detección de pantalla
│   │   ├── unified_recorder.py    # Reemplazar ctypes.windll
│   │   ├── buffering.py             # Sin cambios
│   │   └── sync_manager.py        # Sin cambios
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py         # Sin cambios (tkinter)
│   │   ├── widgets.py             # Sin cambios
│   │   └── dialogs.py             # Sin cambios
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py                # Sin cambios
│   └── utils/
│       ├── __init__.py
│       ├── config.py               # Sin cambios
│       ├── logger.py               # Sin cambios
│       ├── file_manager.py         # Sin cambios
│       └── notifications.py        # Verificar métodos Linux
├── tests/
│   └── [tests adaptados para Linux]
├── examples/
│   └── [ejemplos adaptados]
├── requirements.txt                # Actualizar con mss
├── requirements-dev.txt
├── setup.py
├── README.md                       # Documentación Linux
└── Makefile
```

## Cambios Técnicos Principales

### 1. Captura de Pantalla (`src/core/screen_capture.py`)

**Problema**: `PIL.ImageGrab` no funciona en Linux sin X11 y es lento.

**Solución**: Usar `mss` (Multi-Screen Shot) que es:

- Multiplataforma (Windows, Linux, macOS)
- Más rápido que ImageGrab
- Soporta múltiples monitores nativamente
- No requiere X11 directamente

**Cambios**:

```python
# Reemplazar:
from PIL import ImageGrab
screenshot = ImageGrab.grab()

# Por:
import mss
with mss.mss() as sct:
    screenshot = sct.grab(sct.monitors[0])  # Monitor principal
    # O para región específica:
    screenshot = sct.grab({'top': y, 'left': x, 'width': w, 'height': h})
```

### 2. Detección de Resolución de Pantalla (`src/core/unified_recorder.py`)

**Problema**: `ctypes.windll.user32.GetSystemMetrics()` es específico de Windows.

**Solución**: Usar `mss` para detectar monitores y `tkinter` como fallback.

**Cambios**:

```python
# Reemplazar código Windows-specific:
import ctypes
user32 = ctypes.windll.user32
width = user32.GetSystemMetrics(0)

# Por código multiplataforma:
import mss
with mss.mss() as sct:
    monitor = sct.monitors[0]  # Monitor principal
    width = monitor['width']
    height = monitor['height']
```

### 3. Captura de Audio (`src/core/audio_capture.py`)

**Problema**: Detección de dispositivos puede diferir en Linux.

**Solución**:

- PyAudio funciona en Linux pero requiere dependencias del sistema
- Mejorar detección de dispositivos de audio del sistema (PulseAudio)
- Documentar dependencias del sistema necesarias

**Dependencias del sistema Linux**:

```bash
# Ubuntu/Debian
sudo apt-get install portaudio19-dev python3-pyaudio

# Fedora
sudo dnf install portaudio-devel python3-pyaudio

# Arch
sudo pacman -S portaudio python-pyaudio
```

### 4. Notificaciones (`src/utils/notifications.py`)

**Estado**: Ya tiene soporte Linux con múltiples métodos (paplay, aplay, ffplay).

**Acción**: Verificar que todos los métodos funcionen correctamente y mejorar fallbacks.

### 5. Dependencias del Sistema Linux

**FFmpeg**:

```bash
sudo apt-get install ffmpeg  # Ubuntu/Debian
sudo dnf install ffmpeg      # Fedora
sudo pacman -S ffmpeg        # Arch
```

**Dependencias para captura de pantalla**:

- X11: Ya incluido en la mayoría de distribuciones
- Para Wayland: Usar `mss` que soporta ambos

## Archivos a Modificar

### Archivos Principales:

1. `src/core/screen_capture.py` - Reemplazar ImageGrab por mss
2. `src/core/unified_recorder.py` - Eliminar ctypes.windll, usar mss
3. `requirements.txt` - Agregar `mss>=9.0.0`
4. `README.md` - Documentar instalación Linux y dependencias del sistema

### Archivos Sin Cambios (ya multiplataforma):

- `src/gui/main_window.py` - tkinter funciona en Linux
- `src/cli/main.py` - Sin dependencias OS-specific
- `src/utils/logger.py` - Multiplataforma
- `src/utils/file_manager.py` - Multiplataforma
- `src/core/video_encoder.py` - FFmpeg es multiplataforma
- `src/core/buffering.py` - Multiplataforma

## Plan de Implementación

### Fase 1: Configuración Inicial

1. Crear estructura de directorios
2. Crear `requirements.txt` con dependencias Linux
3. Crear `README.md` con instrucciones Linux
4. Configurar `setup.py` si es necesario

### Fase 2: Reemplazar Captura de Pantalla

1. Modificar `screen_capture.py` para usar `mss`
2. Adaptar métodos de detección de resolución
3. Probar captura de pantalla completa
4. Probar captura de región específica
5. Probar múltiples monitores

### Fase 3: Adaptar Detección de Pantalla

1. Modificar `unified_recorder.py` para eliminar `ctypes.windll`
2. Implementar detección multiplataforma con `mss`
3. Agregar fallback con `tkinter`
4. Probar detección de múltiples monitores

### Fase 4: Adaptar Audio

1. Verificar funcionamiento de PyAudio en Linux
2. Mejorar detección de dispositivos PulseAudio
3. Documentar dependencias del sistema
4. Probar captura de audio del sistema y micrófono

### Fase 5: Verificar Notificaciones

1. Probar métodos de notificación Linux (paplay, aplay, ffplay)
2. Mejorar fallbacks si es necesario
3. Documentar dependencias opcionales

### Fase 6: Testing

1. Crear tests básicos para Linux
2. Probar grabación de pantalla completa
3. Probar grabación de región
4. Probar grabación con audio
5. Probar sincronización video/audio
6. Probar GUI completa

### Fase 7: Documentación

1. Actualizar README con instrucciones Linux
2. Documentar dependencias del sistema
3. Crear guía de instalación
4. Documentar troubleshooting común

## Dependencias del Sistema Linux

### Requeridas:

- Python 3.8+
- FFmpeg
- PortAudio (para PyAudio)
- X11 o Wayland (para captura de pantalla)

### Opcionales (para notificaciones):

- PulseAudio (paplay)
- ALSA (aplay)
- FFmpeg (ffplay)

## Consideraciones Especiales Linux

### Wayland vs X11:

- `mss` funciona en ambos, pero puede requerir permisos especiales en Wayland
- Documentar cómo otorgar permisos de captura de pantalla en Wayland

### Permisos:

- Algunas distribuciones requieren permisos explícitos para captura de pantalla
- Documentar configuración de permisos si es necesario

### Múltiples Monitores:

- `mss` soporta múltiples monitores nativamente
- Implementar selección de monitor en la GUI

## Testing en Linux

### Distribuciones a Probar:

- Ubuntu 20.04+ (X11 y Wayland)
- Debian 11+
- Fedora 35+
- Arch Linux

### Escenarios de Prueba:

1. Captura pantalla completa (un monitor)
2. Captura pantalla completa (múltiples monitores)
3. Captura región específica
4. Captura con audio del sistema
5. Captura con micrófono
6. Grabaciones largas (>1 hora)
7. Sincronización video/audio
8. GUI completa
9. CLI completa

## Notas de Migración

- El código debe ser compatible con ambas plataformas cuando sea posible
- Usar `platform.system()` para detectar el SO y usar el método apropiado
- Mantener fallbacks para máxima compatibilidad
- Documentar claramente las diferencias entre Windows y Linux