"""Ventana principal de la aplicación GUI."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from datetime import timedelta
from pathlib import Path

from ..core.unified_recorder import UnifiedRecorder
from ..core.audio_capture import AudioCapture
from ..utils.config import Config
from ..utils.file_manager import generate_output_filename, validate_output_path
from ..utils.logger import get_logger
from ..utils.notifications import notify_success, notify_error
from .dialogs import AdvancedConfigDialog, LogsDialog, RegionSelectorDialog


class MainWindow:
    """Ventana principal del grabador de video."""

    # Colores modernos
    COLOR_PRIMARY = "#2196F3"
    COLOR_SECONDARY = "#4CAF50"
    COLOR_WARNING = "#FF9800"
    COLOR_ERROR = "#F44336"
    COLOR_BG = "#F5F5F5"
    COLOR_TEXT = "#212121"
    COLOR_BORDER = "#E0E0E0"

    def __init__(self):
        """Inicializar ventana principal."""
        self.root = tk.Tk()
        self.root.title("Grabador de Video v1.0")

        # Obtener dimensiones de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Configurar ventana para ocupar todo el ancho de la pantalla
        # Mantener altura razonable (700px o 80% de la altura, lo que sea menor)
        window_height = min(700, int(screen_height * 0.8))

        # Centrar verticalmente
        y_position = (screen_height - window_height) // 2
        self.root.geometry(f"{screen_width}x{window_height}+0+{y_position}")

        self.root.configure(bg=self.COLOR_BG)

        self.logger = get_logger()
        self.config = Config()
        self.unified_recorder = UnifiedRecorder()
        self.recorder = None

        # Variables de estado
        self.is_recording = False
        self.is_paused = False

        # Variables de configuración
        self.duration_hours = tk.IntVar(value=0)
        self.duration_minutes = tk.IntVar(value=1)
        self.duration_seconds = tk.IntVar(value=0)
        self.fps = tk.IntVar(value=30)
        self.full_screen = tk.BooleanVar(value=True)
        self.region_selected = None

        self.system_audio = tk.BooleanVar(value=True)
        self.microphone_audio = tk.BooleanVar(value=True)
        self.audio_device = tk.StringVar()
        self.sample_rate = tk.StringVar(value="44100")
        self.audio_channels = tk.StringVar(value="Stereo")

        self.output_file = tk.StringVar()
        self.output_format = tk.StringVar(value="MP4")
        self.quality = tk.StringVar(value="Alta")

        # Inicializar GUI
        self._create_widgets()
        self._load_config()
        self._update_audio_devices()

        # Actualizar progreso periódicamente
        self._schedule_progress_update()

    def _create_widgets(self):
        """Crear todos los widgets de la interfaz."""
        # Frame principal con padding
        main_frame = tk.Frame(self.root, bg=self.COLOR_BG, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Grabador de Video v1.0",
            font=("DejaVu Sans", 16, "bold"),
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
        )
        title_label.pack(pady=(0, 20))

        # Sección: Configuración de Grabación
        self._create_recording_config(main_frame)

        # Sección: Configuración de Audio
        self._create_audio_config(main_frame)

        # Sección: Configuración de Salida
        self._create_output_config(main_frame)

        # Sección: Controles
        self._create_controls(main_frame)

        # Sección: Progreso de Grabación
        self._create_progress(main_frame)

    def _create_recording_config(self, parent):
        """Crear sección de configuración de grabación."""
        frame = tk.LabelFrame(
            parent,
            text="Configuración de Grabación",
            font=("DejaVu Sans", 11, "bold"),
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            relief=tk.RIDGE,
            borderwidth=2,
            padx=10,
            pady=10,
        )
        frame.pack(fill=tk.X, pady=5)

        # Duración
        duration_frame = tk.Frame(frame, bg=self.COLOR_BG)
        duration_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            duration_frame,
            text="Duración:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)

        # Horas
        tk.Spinbox(
            duration_frame,
            from_=0,
            to=23,
            textvariable=self.duration_hours,
            width=5,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=2)
        tk.Label(duration_frame, text="h", bg=self.COLOR_BG, fg=self.COLOR_TEXT).pack(
            side=tk.LEFT
        )

        # Minutos
        tk.Spinbox(
            duration_frame,
            from_=0,
            to=59,
            textvariable=self.duration_minutes,
            width=5,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=2)
        tk.Label(duration_frame, text="m", bg=self.COLOR_BG, fg=self.COLOR_TEXT).pack(
            side=tk.LEFT
        )

        # Segundos
        tk.Spinbox(
            duration_frame,
            from_=0,
            to=59,
            textvariable=self.duration_seconds,
            width=5,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=2)
        tk.Label(duration_frame, text="s", bg=self.COLOR_BG, fg=self.COLOR_TEXT).pack(
            side=tk.LEFT
        )

        # Área de grabación
        area_frame = tk.Frame(frame, bg=self.COLOR_BG)
        area_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            area_frame,
            text="Recording Area:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)

        tk.Radiobutton(
            area_frame,
            text="Pantalla completa",
            variable=self.full_screen,
            value=True,
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
            command=self._on_area_change,
        ).pack(side=tk.LEFT, padx=10)

        tk.Radiobutton(
            area_frame,
            text="Región específica",
            variable=self.full_screen,
            value=False,
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
            command=self._on_area_change,
        ).pack(side=tk.LEFT, padx=10)

        self.btn_select_region = tk.Button(
            area_frame,
            text="Seleccionar",
            command=self._select_region,
            state=tk.DISABLED,
            bg=self.COLOR_PRIMARY,
            fg="white",
            font=("DejaVu Sans", 9),
            relief=tk.RAISED,
            padx=10,
            pady=2,
        )
        self.btn_select_region.pack(side=tk.LEFT, padx=5)

        # FPS
        fps_frame = tk.Frame(frame, bg=self.COLOR_BG)
        fps_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            fps_frame,
            text="FPS:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)

        tk.Spinbox(
            fps_frame,
            from_=1,
            to=60,
            textvariable=self.fps,
            width=10,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)
        tk.Label(
            fps_frame, text="frames/segundo", bg=self.COLOR_BG, fg=self.COLOR_TEXT
        ).pack(side=tk.LEFT)

    def _create_audio_config(self, parent):
        """Crear sección de configuración de audio."""
        frame = tk.LabelFrame(
            parent,
            text="Configuración de Audio",
            font=("DejaVu Sans", 11, "bold"),
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            relief=tk.RIDGE,
            borderwidth=2,
            padx=10,
            pady=10,
        )
        frame.pack(fill=tk.X, pady=5)

        # Fuentes de audio
        sources_frame = tk.Frame(frame, bg=self.COLOR_BG)
        sources_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            sources_frame,
            text="Audio Sources:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)

        tk.Checkbutton(
            sources_frame,
            text="Audio del sistema",
            variable=self.system_audio,
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=10)

        tk.Checkbutton(
            sources_frame,
            text="Audio del micrófono",
            variable=self.microphone_audio,
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=10)

        # Dispositivo
        device_frame = tk.Frame(frame, bg=self.COLOR_BG)
        device_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            device_frame,
            text="Dispositivo:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)

        self.audio_device_combo = ttk.Combobox(
            device_frame,
            textvariable=self.audio_device,
            state="readonly",
            width=30,
            font=("DejaVu Sans", 10),
        )
        self.audio_device_combo.pack(side=tk.LEFT, padx=5)

        # Sample Rate
        sample_frame = tk.Frame(frame, bg=self.COLOR_BG)
        sample_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            sample_frame,
            text="Sample Rate:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)

        sample_combo = ttk.Combobox(
            sample_frame,
            textvariable=self.sample_rate,
            values=["44100", "48000", "96000"],
            state="readonly",
            width=15,
            font=("DejaVu Sans", 10),
        )
        sample_combo.pack(side=tk.LEFT, padx=5)
        tk.Label(sample_frame, text="Hz", bg=self.COLOR_BG, fg=self.COLOR_TEXT).pack(
            side=tk.LEFT
        )

        # Canales
        channels_frame = tk.Frame(frame, bg=self.COLOR_BG)
        channels_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            channels_frame,
            text="Canales:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)

        tk.Radiobutton(
            channels_frame,
            text="Mono",
            variable=self.audio_channels,
            value="Mono",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=10)

        tk.Radiobutton(
            channels_frame,
            text="Stereo",
            variable=self.audio_channels,
            value="Stereo",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=10)

    def _create_output_config(self, parent):
        """Crear sección de configuración de salida."""
        frame = tk.LabelFrame(
            parent,
            text="Configuración de Salida",
            font=("DejaVu Sans", 11, "bold"),
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            relief=tk.RIDGE,
            borderwidth=2,
            padx=10,
            pady=10,
        )
        frame.pack(fill=tk.X, pady=5)

        # Archivo
        file_frame = tk.Frame(frame, bg=self.COLOR_BG)
        file_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            file_frame,
            text="Archivo:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)

        file_entry = tk.Entry(
            file_frame,
            textvariable=self.output_file,
            width=40,
            font=("DejaVu Sans", 10),
        )
        file_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        tk.Button(
            file_frame,
            text="Examinar...",
            command=self._browse_output_file,
            bg=self.COLOR_PRIMARY,
            fg="white",
            font=("DejaVu Sans", 9),
            relief=tk.RAISED,
            padx=10,
            pady=2,
        ).pack(side=tk.LEFT, padx=5)

        # Formato
        format_frame = tk.Frame(frame, bg=self.COLOR_BG)
        format_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            format_frame,
            text="Formato:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)

        format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.output_format,
            values=["MP4", "AVI", "MOV", "MKV"],
            state="readonly",
            width=15,
            font=("DejaVu Sans", 10),
        )
        format_combo.pack(side=tk.LEFT, padx=5)

        # Calidad
        quality_frame = tk.Frame(frame, bg=self.COLOR_BG)
        quality_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            quality_frame,
            text="Calidad:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)

        quality_combo = ttk.Combobox(
            quality_frame,
            textvariable=self.quality,
            values=["Alta", "Media", "Baja"],
            state="readonly",
            width=15,
            font=("DejaVu Sans", 10),
        )
        quality_combo.pack(side=tk.LEFT, padx=5)

    def _create_controls(self, parent):
        """Crear sección de controles."""
        frame = tk.Frame(parent, bg=self.COLOR_BG)
        frame.pack(fill=tk.X, pady=10)

        # Botones principales
        controls_frame = tk.Frame(frame, bg=self.COLOR_BG)
        controls_frame.pack(fill=tk.X, pady=5)

        self.btn_start = tk.Button(
            controls_frame,
            text="INICIAR GRABACIÓN",
            command=self._start_recording,
            bg=self.COLOR_SECONDARY,
            fg="white",
            font=("DejaVu Sans", 11, "bold"),
            relief=tk.RAISED,
            padx=20,
            pady=10,
            cursor="hand2",
        )
        self.btn_start.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.btn_stop = tk.Button(
            controls_frame,
            text="DETENER GRABACIÓN",
            command=self._stop_recording,
            bg=self.COLOR_ERROR,
            fg="white",
            font=("DejaVu Sans", 11, "bold"),
            relief=tk.RAISED,
            padx=20,
            pady=10,
            state=tk.DISABLED,
            cursor="hand2",
        )
        self.btn_stop.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.btn_pause = tk.Button(
            controls_frame,
            text="PAUSAR",
            command=self._pause_recording,
            bg=self.COLOR_WARNING,
            fg="white",
            font=("DejaVu Sans", 11, "bold"),
            relief=tk.RAISED,
            padx=20,
            pady=10,
            state=tk.DISABLED,
            cursor="hand2",
        )
        self.btn_pause.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Botones secundarios
        secondary_frame = tk.Frame(frame, bg=self.COLOR_BG)
        secondary_frame.pack(fill=tk.X, pady=5)

        tk.Button(
            secondary_frame,
            text="Configuración Avanzada",
            command=self._show_advanced_config,
            bg=self.COLOR_PRIMARY,
            fg="white",
            font=("DejaVu Sans", 10),
            relief=tk.RAISED,
            padx=15,
            pady=5,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            secondary_frame,
            text="Ver Logs",
            command=self._show_logs,
            bg=self.COLOR_PRIMARY,
            fg="white",
            font=("DejaVu Sans", 10),
            relief=tk.RAISED,
            padx=15,
            pady=5,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=5)

    def _create_progress(self, parent):
        """Crear sección de progreso."""
        frame = tk.LabelFrame(
            parent,
            text="Progreso de Grabación",
            font=("DejaVu Sans", 11, "bold"),
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            relief=tk.RIDGE,
            borderwidth=2,
            padx=10,
            pady=10,
        )
        frame.pack(fill=tk.X, pady=5)

        # Tiempo transcurrido
        elapsed_frame = tk.Frame(frame, bg=self.COLOR_BG)
        elapsed_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            elapsed_frame,
            text="Tiempo transcurrido:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)

        self.elapsed_label = tk.Label(
            elapsed_frame,
            text="00:00:00",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10, "bold"),
        )
        self.elapsed_label.pack(side=tk.LEFT, padx=5)

        # Tiempo restante
        remaining_frame = tk.Frame(frame, bg=self.COLOR_BG)
        remaining_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            remaining_frame,
            text="Tiempo restante:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)

        self.remaining_label = tk.Label(
            remaining_frame,
            text="00:00:00",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10, "bold"),
        )
        self.remaining_label.pack(side=tk.LEFT, padx=5)

        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode="determinate",
        )
        self.progress_bar.pack(fill=tk.X, pady=10, padx=5)

        self.progress_label = tk.Label(
            frame,
            text="0% completado",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 9),
        )
        self.progress_label.pack(pady=2)

        # Frames y audio capturados
        stats_frame = tk.Frame(frame, bg=self.COLOR_BG)
        stats_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            stats_frame,
            text="Frames capturados:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=5)

        self.frames_label = tk.Label(
            stats_frame,
            text="0",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10, "bold"),
        )
        self.frames_label.pack(side=tk.LEFT, padx=5)

        tk.Label(
            stats_frame,
            text="Audio capturado:",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10),
        ).pack(side=tk.LEFT, padx=20)

        self.audio_label = tk.Label(
            stats_frame,
            text="0 MB",
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT,
            font=("DejaVu Sans", 10, "bold"),
        )
        self.audio_label.pack(side=tk.LEFT, padx=5)

    def _load_config(self):
        """Cargar configuración guardada."""
        self.fps.set(self.config.get("fps", 30))
        self.output_format.set(self.config.get("format", "MP4"))
        self.quality.set(self.config.get("quality", "Alta"))
        self.sample_rate.set(str(self.config.get("sample_rate", 44100)))
        channels = self.config.get("audio_channels", 2)
        self.audio_channels.set("Stereo" if channels == 2 else "Mono")

        # Generar nombre de archivo por defecto
        if not self.output_file.get():
            default_file = generate_output_filename(
                extension=self.output_format.get().lower()
            )
            self.output_file.set(default_file)

    def _update_audio_devices(self):
        """Actualizar lista de dispositivos de audio."""
        try:
            audio_capture = AudioCapture()
            devices = audio_capture.get_audio_devices()
            device_names = [f"{d['name']} ({d['index']})" for d in devices]

            if device_names:
                self.audio_device_combo["values"] = device_names
                if not self.audio_device.get():
                    try:
                        default_device = audio_capture.get_default_input_device()
                        self.audio_device.set(
                            f"{default_device['name']} ({default_device['index']})"
                        )
                    except RuntimeError:
                        # No hay dispositivos disponibles (común en WSL)
                        self.audio_device_combo["values"] = [
                            "No hay dispositivos disponibles"
                        ]
                        self.logger.info(
                            "No se encontraron dispositivos de audio (normal en WSL)"
                        )
            else:
                # No hay dispositivos disponibles
                self.audio_device_combo["values"] = ["No hay dispositivos disponibles"]
                self.logger.info(
                    "No se encontraron dispositivos de audio (normal en WSL)"
                )
            audio_capture.close()
        except Exception as e:
            self.logger.warning(f"No se pudieron cargar dispositivos de audio: {e}")
            self.audio_device_combo["values"] = ["Error al cargar dispositivos"]

    def _on_area_change(self):
        """Manejar cambio en selección de área."""
        if self.full_screen.get():
            self.btn_select_region.config(state=tk.DISABLED)
            self.region_selected = None
        else:
            self.btn_select_region.config(state=tk.NORMAL)

    def _select_region(self):
        """Abrir diálogo de selección de región."""
        dialog = RegionSelectorDialog(self.root, self.unified_recorder)
        if dialog.result:
            self.region_selected = dialog.result
            self.logger.info(f"Región seleccionada: {self.region_selected}")

    def _browse_output_file(self):
        """Abrir diálogo para seleccionar archivo de salida."""
        format_ext = self.output_format.get().lower()
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{format_ext}",
            filetypes=[(f"Archivo {format_ext.upper()}", f"*.{format_ext}")],
            initialfile=self.output_file.get(),
        )
        if filename:
            self.output_file.set(filename)

    def _start_recording(self):
        """Iniciar grabación."""
        try:
            self.logger.info("Iniciando grabación desde la GUI...")
            # Validar configuración
            if not self.output_file.get():
                messagebox.showerror("Error", "Debe especificar un archivo de salida")
                return

            if not validate_output_path(self.output_file.get()):
                messagebox.showerror(
                    "Error",
                    "La ruta de salida no es válida o no tiene permisos de escritura",
                )
                return

            # Verificar display (WSL)
            if not self.unified_recorder.screen_capture.has_display:
                response = messagebox.askyesno(
                    "Advertencia - WSL sin X11",
                    "No se detectó un servidor X11. En WSL necesitas:\n\n"
                    "1. Instalar un servidor X11 en Windows (VcXsrv, Xming)\n"
                    "2. Configurar DISPLAY:\n"
                    "   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0\n\n"
                    "¿Deseas continuar de todos modos? (La grabación fallará sin X11)",
                )
                if not response:
                    return

            # Calcular duración
            total_seconds = (
                self.duration_hours.get() * 3600
                + self.duration_minutes.get() * 60
                + self.duration_seconds.get()
            )

            if total_seconds == 0:
                self.logger.debug(
                    "Duración no especificada, grabando sin límite de tiempo."
                )
                total_seconds = None  # Sin límite de tiempo
            else:
                self.logger.debug(
                    f"Duración total de la grabación: {total_seconds} segundos."
                )

            # Crear grabador
            self.recorder = self.unified_recorder.create_recorder(fps=self.fps.get())

            # Configurar región
            if not self.full_screen.get() and self.region_selected:
                self.recorder.set_screen_region(self.region_selected)
                self.logger.debug(
                    f"Grabando región seleccionada: {self.region_selected}"
                )
            else:
                self.logger.debug("Grabando pantalla completa.")

            # Configurar callback de progreso
            self.recorder.set_progress_callback(self._update_progress)

            # Iniciar grabación
            enable_audio = self.system_audio.get() or self.microphone_audio.get()
            audio_device_index = None

            # Verificar que hay dispositivos de audio si está habilitado
            if enable_audio:
                self.logger.info("Audio habilitado por el usuario.")
                try:
                    test_audio = AudioCapture()
                    devices = test_audio.get_audio_devices()
                    test_audio.close()

                    if not devices:
                        self.logger.warning(
                            "Audio habilitado pero no se encontraron dispositivos."
                        )
                        response = messagebox.askyesno(
                            "Sin dispositivos de audio",
                            "No se encontraron dispositivos de audio disponibles.\n\n"
                            "¿Deseas continuar la grabación sin audio?",
                        )
                        if not response:
                            return
                        enable_audio = False
                    elif (
                        self.audio_device.get()
                        and "No hay" not in self.audio_device.get()
                    ):
                        self.logger.debug(
                            f"Dispositivo de audio seleccionado: {self.audio_device.get()}"
                        )
                        # Extraer índice del dispositivo
                        try:
                            device_str = self.audio_device.get()
                            device_index = int(device_str.split("(")[1].split(")")[0])
                            audio_device_index = device_index
                        except:
                            audio_device_index = None
                except Exception as e:
                    self.logger.warning(
                        f"Error al verificar dispositivos de audio: {e}"
                    )
                    enable_audio = False
            else:
                self.logger.info("Audio deshabilitado por el usuario.")

            channels = 2 if self.audio_channels.get() == "Stereo" else 1
            self.logger.debug(
                f"Configuración de audio: Sample Rate={self.sample_rate.get()}, Canales={channels}"
            )

            try:
                self.recorder.start_recording(
                    duration=total_seconds,
                    output_path=self.output_file.get(),
                    format=self.output_format.get().lower(),
                    quality=self.quality.get(),
                    enable_audio=enable_audio,
                    audio_device_index=audio_device_index,
                    sample_rate=int(self.sample_rate.get()),
                    audio_channels=channels,
                )

                self.is_recording = True
                self.is_paused = False

                # Actualizar UI
                self.btn_start.config(state=tk.DISABLED)
                self.btn_stop.config(state=tk.NORMAL)
                self.btn_pause.config(state=tk.NORMAL)

                # Minimizar ventana automáticamente al iniciar grabación
                self.root.after(100, self.root.iconify)

                self.logger.info("Grabación iniciada")
            except Exception as e:
                self.logger.error(f"Error al iniciar grabación: {e}")
                messagebox.showerror("Error", f"No se pudo iniciar la grabación: {e}")
                notify_error()
                # Asegurar que el recorder se limpie
                if self.recorder:
                    try:
                        self.recorder.cleanup()
                    except:
                        pass
                self.recorder = None

        except Exception as e:
            self.logger.error(f"Error al iniciar grabación: {e}")
            messagebox.showerror("Error", f"No se pudo iniciar la grabación: {e}")
            notify_error()

    def _stop_recording(self):
        """Detener grabación."""
        if not self.is_recording:
            return

        try:
            output_file = self.recorder.stop_recording()

            self.is_recording = False
            self.is_paused = False

            # Restaurar ventana si estaba minimizada
            if self.root.state() == "iconic":
                self.root.deiconify()
                self.root.lift()  # Traer al frente

            # Actualizar UI
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.DISABLED)

            # Resetear progreso
            self._reset_progress()

            if output_file:
                messagebox.showinfo("Éxito", f"Grabación completada:\n{output_file}")
                notify_success()
                self.logger.info(f"Grabación guardada en: {output_file}")
            else:
                messagebox.showwarning(
                    "Advertencia", "La grabación se detuvo pero no se generó archivo"
                )

        except Exception as e:
            self.logger.error(f"Error al detener grabación: {e}")
            messagebox.showerror("Error", f"Error al detener grabación: {e}")
            notify_error()

    def _pause_recording(self):
        """Pausar/Reanudar grabación."""
        if not self.is_recording:
            return

        if self.is_paused:
            self.recorder.resume_recording()
            self.is_paused = False
            self.btn_pause.config(text="PAUSAR")
        else:
            self.recorder.pause_recording()
            self.is_paused = True
            self.btn_pause.config(text="REANUDAR")

    def _update_progress(self, elapsed, remaining, frames, audio_mb):
        """Actualizar progreso de grabación."""
        # Actualizar tiempo transcurrido
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        self.elapsed_label.config(text=elapsed_str)

        # Actualizar tiempo restante
        if remaining is not None:
            remaining_str = str(timedelta(seconds=int(remaining)))
            self.remaining_label.config(text=remaining_str)

            # Calcular porcentaje
            total = elapsed + remaining
            if total > 0:
                percentage = (elapsed / total) * 100
                self.progress_var.set(percentage)
                self.progress_label.config(text=f"{percentage:.1f}% completado")
        else:
            self.remaining_label.config(text="--:--:--")
            self.progress_label.config(text="Grabando...")

        # Actualizar frames y audio
        self.frames_label.config(text=str(frames))
        self.audio_label.config(text=f"{audio_mb:.2f} MB")

    def _reset_progress(self):
        """Resetear indicadores de progreso."""
        self.elapsed_label.config(text="00:00:00")
        self.remaining_label.config(text="00:00:00")
        self.progress_var.set(0)
        self.progress_label.config(text="0% completado")
        self.frames_label.config(text="0")
        self.audio_label.config(text="0 MB")

    def _schedule_progress_update(self):
        """Programar actualización periódica de progreso."""
        if self.is_recording and self.recorder:
            try:
                elapsed = self.recorder.get_elapsed_time()
                remaining = self.recorder.get_remaining_time()
                frames = self.recorder.frames_captured
                audio_mb = 0.0
                if self.recorder.audio_capture:
                    audio_mb = self.recorder.audio_capture.get_captured_size_mb()

                self._update_progress(elapsed, remaining, frames, audio_mb)
            except:
                pass

        self.root.after(100, self._schedule_progress_update)

    def _show_advanced_config(self):
        """Mostrar diálogo de configuración avanzada."""
        dialog = AdvancedConfigDialog(self.root, self.config)
        if dialog.result:
            self._load_config()

    def _show_logs(self):
        """Mostrar diálogo de logs."""
        LogsDialog(self.root, self.logger)

    def run(self):
        """Ejecutar aplicación."""
        try:
            self.root.mainloop()
        finally:
            if self.recorder:
                self.recorder.cleanup()
            self.unified_recorder.cleanup()
