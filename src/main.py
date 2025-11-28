"""Punto de entrada principal de la aplicación."""

import sys
import os
import argparse
import logging

# Suprimir warnings de ALSA a nivel de aplicación
os.environ['PYTHONWARNINGS'] = 'ignore'
# Suprimir mensajes de ALSA usando variable de entorno
os.environ['ALSA_CARD'] = '0'
# Redirigir stderr de ALSA a /dev/null
os.environ['ALSA_PCM_NAME'] = 'default'

from .gui.main_window import MainWindow
from .utils.logger import setup_logger


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Grabador de Video y Audio")
    parser.add_argument(
        '--cli',
        action='store_true',
        help='Ejecutar en modo CLI en lugar de GUI'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Habilitar logging detallado (DEBUG)'
    )
    
    # Parsear argumentos conocidos para separar los globales de los del módulo
    args, remaining_argv = parser.parse_known_args()
    
    # Configurar logger
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger(level=log_level)
    logger.debug("Logging activado en nivel DEBUG.")
    
    if args.cli:
        # Ejecutar CLI y pasarle los argumentos restantes
        from .cli.main import main as cli_main
        cli_main(remaining_argv)
    else:
        # Ejecutar GUI
        try:
            app = MainWindow()
            app.run()
        except KeyboardInterrupt:
            logger.info("Aplicación interrumpida por el usuario")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error al ejecutar aplicación: {e}", exc_info=True)
            sys.exit(1)


if __name__ == '__main__':
    main()
