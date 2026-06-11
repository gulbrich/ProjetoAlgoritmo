"""
main.py
-------
Ponto de entrada do sistema de precificacao de produtos importados.

Para trocar de interfaces, basta alterar o import abaixo:
    from interfaces.cli import menu   <- terminal (atual)
    from interfaces.gui import menu   <- tkinter (futuro)
    from interfaces.web import menu   <- flask/streamlit (futuro)
"""

from interfaces.cli import menu

if __name__ == "__main__":
    menu()