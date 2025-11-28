"""Widgets personalizados para la GUI."""

import tkinter as tk
from tkinter import ttk


class TimeEntry(tk.Frame):
    """Widget para entrada de tiempo (horas, minutos, segundos)."""
    
    def __init__(self, parent, **kwargs):
        """
        Inicializar widget de tiempo.
        
        Args:
            parent: Widget padre.
            **kwargs: Argumentos adicionales.
        """
        super().__init__(parent, **kwargs)
        
        self.hours_var = tk.IntVar(value=0)
        self.minutes_var = tk.IntVar(value=0)
        self.seconds_var = tk.IntVar(value=0)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crear widgets internos."""
        # Horas
        tk.Spinbox(
            self,
            from_=0,
            to=23,
            textvariable=self.hours_var,
            width=5
        ).pack(side=tk.LEFT, padx=2)
        tk.Label(self, text="h").pack(side=tk.LEFT)
        
        # Minutos
        tk.Spinbox(
            self,
            from_=0,
            to=59,
            textvariable=self.minutes_var,
            width=5
        ).pack(side=tk.LEFT, padx=2)
        tk.Label(self, text="m").pack(side=tk.LEFT)
        
        # Segundos
        tk.Spinbox(
            self,
            from_=0,
            to=59,
            textvariable=self.seconds_var,
            width=5
        ).pack(side=tk.LEFT, padx=2)
        tk.Label(self, text="s").pack(side=tk.LEFT)
    
    def get_total_seconds(self) -> int:
        """
        Obtener tiempo total en segundos.
        
        Returns:
            Tiempo total en segundos.
        """
        return (
            self.hours_var.get() * 3600 +
            self.minutes_var.get() * 60 +
            self.seconds_var.get()
        )
    
    def set_total_seconds(self, seconds: int):
        """
        Establecer tiempo total desde segundos.
        
        Args:
            seconds: Tiempo total en segundos.
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        self.hours_var.set(hours)
        self.minutes_var.set(minutes)
        self.seconds_var.set(secs)


class ProgressBarWithLabel(tk.Frame):
    """Barra de progreso con etiqueta."""
    
    def __init__(self, parent, text: str = "", **kwargs):
        """
        Inicializar barra de progreso con etiqueta.
        
        Args:
            parent: Widget padre.
            text: Texto de la etiqueta.
            **kwargs: Argumentos adicionales.
        """
        super().__init__(parent, **kwargs)
        
        self.text = text
        self.progress_var = tk.DoubleVar()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Crear widgets internos."""
        if self.text:
            tk.Label(self, text=self.text).pack(side=tk.LEFT, padx=5)
        
        self.progress_bar = ttk.Progressbar(
            self,
            variable=self.progress_var,
            maximum=100,
            length=300,
            mode='determinate'
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.label = tk.Label(self, text="0%")
        self.label.pack(side=tk.LEFT, padx=5)
    
    def set_progress(self, value: float, text: str = None):
        """
        Establecer progreso.
        
        Args:
            value: Valor del progreso (0-100).
            text: Texto opcional para mostrar.
        """
        self.progress_var.set(min(100, max(0, value)))
        if text:
            self.label.config(text=text)
        else:
            self.label.config(text=f"{value:.1f}%")

