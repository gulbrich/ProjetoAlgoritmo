"""
main.py
-------
Ponto de entrada do sistema de precificação de produtos importados.

Uso:
    python main.py        -> interface gráfica (padrão)
    python main.py --cli  -> interface de linha de comando
"""

import sys
import os

# Garante que o diretório raiz do projeto está no sys.path,
# permitindo imports absolutos como 'from modulos.x import y'
# independente de onde o script é executado.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    if "--cli" in sys.argv:
        from interfaces.cli import menu
    else:
        from interfaces.gui import menu
    menu()


if __name__ == "__main__":
    main()