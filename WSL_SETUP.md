# Configuración para WSL (Windows Subsystem for Linux)

Este documento explica cómo configurar el grabador de video para funcionar en WSL.

## Limitaciones de WSL

WSL tiene algunas limitaciones que afectan al grabador:

1. **Sin servidor X11 por defecto**: No puede capturar pantalla sin configuración adicional
2. **Sin dispositivos de audio**: Los warnings de ALSA son normales y no afectan la funcionalidad

## Configuración de X11 para Captura de Pantalla

### Opción 1: VcXsrv (Recomendado)

1. **Instalar VcXsrv en Windows:**
   - Descargar desde: https://sourceforge.net/projects/vcxsrv/
   - Instalar y ejecutar XLaunch

2. **Configurar XLaunch:**
   - Seleccionar "Multiple windows"
   - Marcar "Disable access control"
   - Finalizar la configuración

3. **Configurar DISPLAY en WSL:**
   ```bash
   # Agregar al ~/.bashrc o ~/.zshrc
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
   ```

4. **Verificar:**
   ```bash
   echo $DISPLAY
   # Debe mostrar algo como: 172.x.x.x:0.0
   ```

### Opción 2: Xming

1. **Instalar Xming:**
   - Descargar desde: https://sourceforge.net/projects/xming/
   - Instalar y ejecutar

2. **Configurar DISPLAY:**
   ```bash
   export DISPLAY=:0.0
   ```

## Configuración de Audio (Opcional)

Para captura de audio en WSL, necesitas:

1. **Instalar PulseAudio en Windows:**
   - Descargar desde: https://www.freedesktop.org/wiki/Software/PulseAudio/Ports/Windows/Support/
   - O usar WSLg (disponible en Windows 11)

2. **Configurar PulseAudio:**
   ```bash
   export PULSE_SERVER=tcp:localhost
   ```

## Uso en WSL

Una vez configurado X11:

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar aplicación
make run
```

## Notas

- Los warnings de ALSA son normales en WSL y no afectan la funcionalidad
- Si no configuras X11, la captura de pantalla no funcionará
- La captura de audio puede no funcionar sin configuración adicional de PulseAudio
- WSL2 es recomendado sobre WSL1 para mejor rendimiento

## Solución de Problemas

### Error: "XOpenDisplay() failed"

- Verifica que VcXsrv o Xming estén ejecutándose
- Verifica que DISPLAY esté configurado correctamente
- Prueba: `xeyes` o `xclock` para verificar X11

### Warnings de ALSA

- Son normales en WSL
- No afectan la funcionalidad si no usas audio
- Para audio, configura PulseAudio

### No se puede capturar pantalla

- Asegúrate de que el servidor X11 esté ejecutándose
- Verifica DISPLAY con `echo $DISPLAY`
- Prueba capturar con: `import mss; mss.mss().grab(mss.mss().monitors[1])`

