# Grabador de Video y Audio para Linux

Un grabador de pantalla y sonido completo desarrollado en Python para Linux, que permite capturar video de la pantalla junto con audio del sistema o micrófono.

## Características

- **Captura de pantalla**: Pantalla completa o región específica usando `mss` (compatible con X11 y Wayland)
- **Captura de audio**: Audio del sistema y/o micrófono con PyAudio
- **Configuración flexible**: FPS, duración, dispositivos de audio
- **Interfaz gráfica moderna**: GUI intuitiva con tkinter mejorada
- **Interfaz de línea de comandos**: Para automatización
- **Formatos de salida**: MP4, AVI, MOV, MKV
- **Sincronización**: Video y audio perfectamente sincronizados
- **Notificaciones de sonido**: Alertas auditivas cuando termina la grabación
- **Multiplataforma**: Compatible con Linux (X11 y Wayland)

## Requisitos

### Sistema

- Python 3.8 o superior
- FFmpeg instalado en el sistema
- PortAudio (para captura de audio)
- X11 o Wayland (para captura de pantalla)

### Dependencias del Sistema

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg portaudio19-dev python3-pyaudio
```

#### Fedora:
```bash
sudo dnf install ffmpeg portaudio-devel python3-pyaudio
```

#### Arch Linux:
```bash
sudo pacman -S ffmpeg portaudio python-pyaudio
```

## Instalación Rápida

### Opción 1: Usando Makefile (Recomendado)

```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd grabador_video_linux

# Instalar dependencias del sistema (requiere sudo)
make install

# Setup completo (crea venv e instala dependencias Python)
make setup

# Verificar que todo esté instalado correctamente
make check-deps
```

### Opción 2: Instalación Manual

```bash
# 1. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias Python
pip install --upgrade pip
pip install -r requirements.txt

# 3. Instalar dependencias del sistema (ver arriba)
```

## Uso

### Interfaz Gráfica (GUI)

```bash
# Usando Makefile (recomendado)
make run

# Sin warnings de ALSA (útil en WSL)
make run-silent

# O manualmente
source venv/bin/activate
python -m src.main

# O usando el script silencioso
./run_silent.sh
```

### Interfaz de Línea de Comandos (CLI)

```bash
# Usando Makefile
make run-cli

# O manualmente con opciones personalizadas
source venv/bin/activate
python -m src.cli.main --duration 60 --output video.mp4 --fps 30 --format mp4 --quality Alta

# Con audio
python -m src.cli.main --duration 30 --audio --sample-rate 44100 --channels 2

# Capturar región específica
python -m src.cli.main --duration 10 --region 100,100,800,600
```

### Como Módulo Python

```python
from src.core.recorder_manager import VideoRecorder

# Crear grabador
recorder = VideoRecorder()

# Configurar región (opcional)
recorder.set_screen_region((0, 0, 1920, 1080))

# Iniciar grabación
recorder.start_recording(
    duration=60,
    output_path="mi_video.mp4",
    format="mp4",
    quality="Alta",
    enable_audio=True
)

# Detener grabación
output_file = recorder.stop_recording()
recorder.cleanup()
```

## Comandos Makefile

El proyecto incluye un Makefile con comandos útiles:

### Setup y Configuración

- `make install` - Instalar dependencias del sistema (FFmpeg, PortAudio)
- `make venv` - Crear entorno virtual
- `make setup` - Setup completo (venv + dependencias Python)
- `make check-deps` - Verificar dependencias del sistema

### Ejecución

- `make run` - Ejecutar aplicación GUI
- `make run-cli` - Ejecutar CLI con parámetros de ejemplo
- `make test` - Ejecutar todos los tests
- `make test-gui` - Ejecutar tests específicos de GUI

### Desarrollo

- `make format` - Formatear código con black
- `make lint` - Verificar código con linters
- `make clean` - Limpiar archivos temporales
- `make help` - Mostrar ayuda con todos los comandos

## Configuración

### Parámetros de Video

- **FPS**: Frames por segundo (por defecto: 30, rango: 1-60)
- **Región**: Coordenadas (x, y, width, height) para captura parcial
- **Resolución**: Automática según la pantalla
- **Monitor**: Selección de monitor en sistemas multi-pantalla

### Parámetros de Audio

- **Sample Rate**: Tasa de muestreo (44100, 48000, 96000 Hz)
- **Canales**: Mono (1) o Stereo (2)
- **Dispositivo**: Selección de dispositivo de entrada
- **Fuentes**: Audio del sistema y/o micrófono

### Formatos y Calidad

- **Formatos**: MP4, AVI, MOV, MKV
- **Calidad**: Alta, Media, Baja (afecta bitrate y compresión)

## Estructura del Proyecto

```
grabador_video_linux/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Punto de entrada principal
│   ├── core/
│   │   ├── screen_capture.py      # Captura con mss (Linux-compatible)
│   │   ├── audio_capture.py       # Captura de audio con PyAudio
│   │   ├── video_encoder.py       # Codificación con FFmpeg
│   │   ├── recorder_manager.py    # Gestor principal de grabación
│   │   ├── unified_recorder.py    # Grabador unificado multiplataforma
│   │   ├── buffering.py           # Sistema de buffers
│   │   └── sync_manager.py        # Sincronización video/audio
│   ├── gui/
│   │   ├── main_window.py         # Ventana principal mejorada
│   │   ├── widgets.py             # Widgets personalizados
│   │   └── dialogs.py             # Diálogos (configuración, logs, región)
│   ├── cli/
│   │   └── main.py                # Interfaz de línea de comandos
│   └── utils/
│       ├── config.py              # Gestión de configuración
│       ├── logger.py              # Sistema de logging
│       ├── file_manager.py        # Gestión de archivos
│       └── notifications.py       # Notificaciones de sonido
├── tests/                         # Tests unitarios e integración
├── requirements.txt               # Dependencias Python
├── requirements-dev.txt           # Dependencias de desarrollo
├── Makefile                       # Comandos rápidos
├── .gitignore                     # Archivos a ignorar
└── README.md                      # Este archivo
```

## Notificaciones de Sonido

El grabador incluye un sistema de notificaciones de sonido que se reproduce automáticamente cuando:

- ✅ **Grabación completada exitosamente**: Sonido de éxito
- ❌ **Error durante la grabación**: Sonido de error  
- ⚠️ **Advertencias o problemas menores**: Sonido de advertencia

### Compatibilidad Linux

Las notificaciones funcionan en Linux usando múltiples métodos (en orden de preferencia):
- PulseAudio (`paplay`)
- ALSA (`aplay`)
- FFmpeg (`ffplay`)

## Desarrollo

### Instalar dependencias de desarrollo

```bash
make setup  # O manualmente: pip install -r requirements-dev.txt
```

### Ejecutar tests

```bash
make test
# O manualmente: pytest tests/ -v
```

### Formatear código

```bash
make format
# O manualmente: black src/ tests/
```

### Verificar código

```bash
make lint
# O manualmente: pylint src/ && flake8 src/
```

## Uso en WSL (Windows Subsystem for Linux)

Si estás usando WSL, consulta el archivo [WSL_SETUP.md](WSL_SETUP.md) para instrucciones detalladas.

**Resumen rápido:**
1. Instala un servidor X11 en Windows (VcXsrv o Xming)
2. Configura DISPLAY: `export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0`
3. Los warnings de ALSA son normales y no afectan la funcionalidad

## Solución de Problemas

### Error: "FFmpeg no encontrado"

```bash
# Verificar instalación
ffmpeg -version

# Si no está instalado
make install  # O instalar manualmente según tu distribución
```

### Error: "XOpenDisplay() failed" (WSL)

Este error ocurre en WSL sin servidor X11 configurado. Ver [WSL_SETUP.md](WSL_SETUP.md) para solución.

### Warnings de ALSA (WSL)

Los warnings de ALSA son normales en WSL y no afectan la funcionalidad. Pueden ignorarse si no usas captura de audio.

### Error: "PyAudio no funciona"

```bash
# Verificar que PortAudio esté instalado
make install  # Instala portaudio19-dev o equivalente

# Verificar en Python
python -c "import pyaudio; print('OK')"
```

### Error: "No se puede capturar pantalla"

- **X11**: Debe funcionar automáticamente
- **Wayland**: Puede requerir permisos especiales. Verifica la configuración de tu compositor de ventanas

### Error: "Permisos insuficientes"

Algunas distribuciones requieren permisos explícitos para captura de pantalla. En Wayland, verifica la configuración de permisos de tu entorno de escritorio.

### Error: "No se puede acceder al dispositivo de audio"

1. Verifica que el dispositivo esté conectado
2. Verifica permisos de audio (puede requerir agregar usuario al grupo `audio`)
3. Verifica que PulseAudio o ALSA estén funcionando

## Testing

### Tests Automatizados

```bash
# Ejecutar todos los tests
make test

# Tests específicos
pytest tests/test_screen_capture.py -v
pytest tests/test_audio_capture.py -v
pytest tests/test_recorder.py -v
pytest tests/test_integration.py -v
```

### Verificación Manual

1. Ejecutar `make setup` y verificar instalación
2. Ejecutar `make check-deps` y verificar dependencias
3. Ejecutar `make run` y verificar GUI
4. Realizar grabación de prueba (10 segundos)
5. Verificar archivo de salida generado
6. Probar CLI con `make run-cli`

## Características Técnicas

- **Captura de pantalla**: Usa `mss` (Multi-Screen Shot) - más rápido que PIL.ImageGrab y compatible con Linux
- **Captura de audio**: PyAudio con soporte para PulseAudio y ALSA
- **Codificación**: FFmpeg para máxima compatibilidad y calidad
- **Sincronización**: Sistema de buffers y sincronización precisa video/audio
- **Multi-monitor**: Soporte nativo para múltiples monitores

## Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Autor

Jorge - [jorge@example.com](mailto:jorge@example.com)

## Changelog

### v1.0.0 (Linux)

- ✨ **Nuevo**: Versión completa para Linux
- 🖥️ Compatibilidad con X11 y Wayland
- 🎥 Captura de pantalla con `mss` (más rápido y compatible)
- 🔊 Captura de audio con PyAudio (PulseAudio/ALSA)
- 🎨 GUI moderna mejorada con mejor UX
- 📝 CLI completa con todas las opciones
- 🧪 Tests unitarios e integración
- 🔧 Makefile para comandos rápidos
- 📚 Documentación completa
