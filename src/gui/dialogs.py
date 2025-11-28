"""Diálogos de la aplicación."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Optional, Tuple
from ..core.unified_recorder import UnifiedRecorder
from ..utils.config import Config


class AdvancedConfigDialog:
    """Diálogo de configuración avanzada."""
    
    def __init__(self, parent, config: Config):
        """
        Inicializar diálogo.
        
        Args:
            parent: Ventana padre.
            config: Instancia de configuración.
        """
        self.config = config
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configuración Avanzada")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._load_config()
        
        # Centrar ventana
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.dialog.wait_window()
    
    def _create_widgets(self):
        """Crear widgets del diálogo."""
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configuraciones avanzadas aquí
        tk.Label(
            main_frame,
            text="Configuración Avanzada",
            font=("DejaVu Sans", 14, "bold")
        ).pack(pady=10)
        
        tk.Label(
            main_frame,
            text="Esta sección permite configuraciones avanzadas del grabador.",
            font=("DejaVu Sans", 10)
        ).pack(pady=10)
        
        # Botones
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame,
            text="Guardar",
            command=self._save,
            bg="#4CAF50",
            fg="white",
            font=("DejaVu Sans", 10),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Cancelar",
            command=self._cancel,
            bg="#F44336",
            fg="white",
            font=("DejaVu Sans", 10),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
    
    def _load_config(self):
        """Cargar configuración actual."""
        pass
    
    def _save(self):
        """Guardar configuración."""
        self.result = True
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancelar."""
        self.result = None
        self.dialog.destroy()


class LogsDialog:
    """Diálogo para mostrar logs."""
    
    def __init__(self, parent, logger):
        """
        Inicializar diálogo de logs.
        
        Args:
            parent: Ventana padre.
            logger: Logger para obtener logs.
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Logs del Sistema")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        
        self._create_widgets()
        
        # Centrar ventana
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Crear widgets del diálogo."""
        main_frame = tk.Frame(self.dialog, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            main_frame,
            text="Logs del Sistema",
            font=("DejaVu Sans", 12, "bold")
        ).pack(pady=5)
        
        # Área de texto con scroll
        self.text_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            font=("Courier", 9)
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Mostrar logs disponibles
        self.text_area.insert(tk.END, "Logs del sistema:\n")
        self.text_area.insert(tk.END, "Los logs se mostrarán aquí cuando estén disponibles.\n")
        self.text_area.config(state=tk.DISABLED)
        
        # Botón cerrar
        tk.Button(
            main_frame,
            text="Cerrar",
            command=self.dialog.destroy,
            bg="#2196F3",
            fg="white",
            font=("DejaVu Sans", 10),
            padx=20,
            pady=5
        ).pack(pady=5)


class RegionSelectorDialog:
    """Diálogo para seleccionar región de grabación."""
    
    def __init__(self, parent, unified_recorder: UnifiedRecorder):
        """
        Inicializar diálogo de selección de región.
        
        Args:
            parent: Ventana padre.
            unified_recorder: Instancia del grabador unificado.
        """
        self.unified_recorder = unified_recorder
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Seleccionar Región")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        
        # Centrar ventana
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.dialog.wait_window()
    
    def _create_widgets(self):
        """Crear widgets del diálogo."""
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            main_frame,
            text="Seleccionar Región de Grabación",
            font=("DejaVu Sans", 12, "bold")
        ).pack(pady=10)
        
        tk.Label(
            main_frame,
            text="Ingrese las coordenadas de la región:",
            font=("DejaVu Sans", 10)
        ).pack(pady=5)
        
        # Campos de entrada
        coords_frame = tk.Frame(main_frame)
        coords_frame.pack(pady=10)
        
        tk.Label(coords_frame, text="X:").grid(row=0, column=0, padx=5, pady=5)
        self.x_var = tk.IntVar(value=0)
        tk.Entry(coords_frame, textvariable=self.x_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(coords_frame, text="Y:").grid(row=0, column=2, padx=5, pady=5)
        self.y_var = tk.IntVar(value=0)
        tk.Entry(coords_frame, textvariable=self.y_var, width=10).grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(coords_frame, text="Ancho:").grid(row=1, column=0, padx=5, pady=5)
        self.width_var = tk.IntVar(value=1920)
        tk.Entry(coords_frame, textvariable=self.width_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(coords_frame, text="Alto:").grid(row=1, column=2, padx=5, pady=5)
        self.height_var = tk.IntVar(value=1080)
        tk.Entry(coords_frame, textvariable=self.height_var, width=10).grid(row=1, column=3, padx=5, pady=5)
        
        # Botones
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame,
            text="Aceptar",
            command=self._accept,
            bg="#4CAF50",
            fg="white",
            font=("DejaVu Sans", 10),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Cancelar",
            command=self._cancel,
            bg="#F44336",
            fg="white",
            font=("DejaVu Sans", 10),
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
    
    def _accept(self):
        """Aceptar selección."""
        x = self.x_var.get()
        y = self.y_var.get()
        width = self.width_var.get()
        height = self.height_var.get()
        
        if width > 0 and height > 0:
            self.result = (x, y, width, height)
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", "El ancho y alto deben ser mayores que 0")
    
    def _cancel(self):
        """Cancelar."""
        self.result = None
        self.dialog.destroy()

