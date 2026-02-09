# run.py
#!/usr/bin/env python3
"""
BomApettite - Sistema de Pedidos QR para Restaurantes
Entry point principal del proyecto
"""

import sys
from pathlib import Path

# Asegurar que el directorio raíz esté en el path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from desktop.main import main

if __name__ == "__main__":
    main()