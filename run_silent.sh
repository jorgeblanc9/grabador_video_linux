#!/bin/bash
# Script para ejecutar la aplicación suprimiendo warnings de ALSA

# Redirigir stderr a /dev/null para suprimir warnings de ALSA
exec 2>/dev/null

# Ejecutar la aplicación
cd "$(dirname "$0")"
source venv/bin/activate
python -m src.main "$@"

