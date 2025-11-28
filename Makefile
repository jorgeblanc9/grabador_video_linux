.PHONY: help install venv setup check-deps run run-cli test test-gui format lint clean

# Variables
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

# Colores para output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(GREEN)Grabador de Video Linux - Comandos disponibles:$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup y Configuración:$(NC)"
	@echo "  make install      - Instalar dependencias del sistema (FFmpeg, PortAudio)"
	@echo "  make venv         - Crear entorno virtual"
	@echo "  make setup        - Setup completo (venv + dependencias Python)"
	@echo "  make check-deps   - Verificar dependencias del sistema"
	@echo ""
	@echo "$(YELLOW)Ejecución (use ARGS=\"--verbose\" para logs detallados):$(NC)"
	@echo "  make run          - Ejecutar aplicación GUI"
	@echo "  make run-silent   - Ejecutar aplicación GUI (sin warnings de ALSA)"
	@echo "  make run-cli      - Ejecutar CLI con parámetros de ejemplo"
	@echo "  make test         - Ejecutar todos los tests"
	@echo "  make test-gui     - Ejecutar tests específicos de GUI"
	@echo ""
	@echo "$(YELLOW)Desarrollo:$(NC)"
	@echo "  make format       - Formatear código con black"
	@echo "  make lint         - Verificar código con linters"
	@echo "  make clean        - Limpiar archivos temporales"
	@echo "  make help         - Mostrar esta ayuda"

install:
	@echo "$(GREEN)Instalando dependencias del sistema...$(NC)"
	@if command -v apt-get > /dev/null; then \
		echo "$(YELLOW)Detectado: Debian/Ubuntu$(NC)"; \
		sudo apt-get update && sudo apt-get install -y ffmpeg portaudio19-dev python3-pyaudio; \
	elif command -v dnf > /dev/null; then \
		echo "$(YELLOW)Detectado: Fedora$(NC)"; \
		sudo dnf install -y ffmpeg portaudio-devel python3-pyaudio; \
	elif command -v pacman > /dev/null; then \
		echo "$(YELLOW)Detectado: Arch Linux$(NC)"; \
		sudo pacman -S --noconfirm ffmpeg portaudio python-pyaudio; \
	else \
		echo "$(RED)No se pudo detectar el gestor de paquetes. Instala manualmente:$(NC)"; \
		echo "  - FFmpeg"; \
		echo "  - PortAudio (portaudio19-dev o portaudio-devel)"; \
		echo "  - python3-pyaudio"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Dependencias del sistema instaladas$(NC)"

venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(GREEN)Creando entorno virtual...$(NC)"; \
		$(PYTHON) -m venv $(VENV); \
		echo "$(GREEN)✓ Entorno virtual creado$(NC)"; \
	else \
		echo "$(YELLOW)Entorno virtual ya existe$(NC)"; \
	fi

setup: venv
	@echo "$(GREEN)Instalando dependencias Python...$(NC)"
	@$(VENV_PIP) install --upgrade pip
	@$(VENV_PIP) install -r requirements.txt
	@if [ -f requirements-dev.txt ]; then \
		$(VENV_PIP) install -r requirements-dev.txt; \
	fi
	@echo "$(GREEN)✓ Setup completo$(NC)"

check-deps:
	@echo "$(GREEN)Verificando dependencias...$(NC)"
	@echo -n "Python: "; $(PYTHON) --version || (echo "$(RED)✗ Python no encontrado$(NC)" && exit 1)
	@echo -n "FFmpeg: "; ffmpeg -version > /dev/null 2>&1 && echo "$(GREEN)✓$(NC)" || (echo "$(RED)✗ FFmpeg no encontrado. Ejecuta: make install$(NC)" && exit 1)
	@if [ -d "$(VENV)" ]; then \
		echo -n "PyAudio: "; $(VENV_PYTHON) -c "import pyaudio" > /dev/null 2>&1 && echo "$(GREEN)✓$(NC)" || (echo "$(RED)✗ PyAudio no encontrado. Ejecuta: make setup$(NC)" && exit 1); \
	else \
		echo "$(YELLOW)Entorno virtual no encontrado. Ejecuta: make setup$(NC)"; \
	fi
	@echo "$(GREEN)✓ Todas las dependencias están instaladas$(NC)"

run: venv
	@if [ ! -f "$(VENV_BIN)/python" ]; then \
		echo "$(RED)Error: Entorno virtual no configurado. Ejecuta: make setup$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Ejecutando aplicación GUI...$(NC)"
	@echo "$(YELLOW)Nota: Los warnings de ALSA son normales en WSL y pueden ignorarse$(NC)"
	@$(VENV_BIN)/python -m src.main $(ARGS)

run-silent: venv
	@if [ ! -f "$(VENV_BIN)/python" ]; then \
		echo "$(RED)Error: Entorno virtual no configurado. Ejecuta: make setup$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Ejecutando aplicación GUI (sin warnings de ALSA)...$(NC)"
	@$(VENV_BIN)/python -m src.main $(ARGS) 2>/dev/null

run-cli: venv
	@if [ ! -f "$(VENV_BIN)/python" ]; then \
		echo "$(RED)Error: Entorno virtual no configurado. Ejecuta: make setup$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Ejecutando CLI...$(NC)"
	@$(VENV_BIN)/python -m src.main --cli --duration 10 --output test_cli.mp4 $(ARGS)

test: venv
	@if [ ! -f "$(VENV_BIN)/python" ]; then \
		echo "$(RED)Error: Entorno virtual no configurado. Ejecuta: make setup$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Ejecutando tests...$(NC)"
	@$(VENV_BIN)/python -m pytest tests/ -v

test-gui: venv
	@if [ ! -f "$(VENV_BIN)/python" ]; then \
		echo "$(RED)Error: Entorno virtual no configurado. Ejecuta: make setup$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Ejecutando tests de GUI...$(NC)"
	@$(VENV_BIN)/python -m pytest tests/test_gui.py -v || echo "$(YELLOW)No hay tests de GUI específicos$(NC)"

format: venv
	@if [ ! -f "$(VENV_BIN)/black" ]; then \
		echo "$(YELLOW)Instalando black...$(NC)"; \
		$(VENV_PIP) install black; \
	fi
	@echo "$(GREEN)Formateando código...$(NC)"
	@$(VENV_BIN)/black src/ tests/ || echo "$(YELLOW)Black no disponible$(NC)"

lint: venv
	@if [ ! -f "$(VENV_BIN)/pylint" ]; then \
		echo "$(YELLOW)Instalando linters...$(NC)"; \
		$(VENV_PIP) install pylint flake8; \
	fi
	@echo "$(GREEN)Verificando código...$(NC)"
	@$(VENV_BIN)/pylint src/ || echo "$(YELLOW)Pylint encontró problemas (continuando...)$(NC)"
	@$(VENV_BIN)/flake8 src/ --max-line-length=120 || echo "$(YELLOW)Flake8 encontró problemas (continuando...)$(NC)"

clean:
	@echo "$(GREEN)Limpiando archivos temporales...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.log" -delete 2>/dev/null || true
	@find . -type f -name "test_*.mp4" -delete 2>/dev/null || true
	@find . -type f -name "grabacion_*.mp4" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Limpieza completada$(NC)"

