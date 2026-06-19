"""
gui.py
------
Janela principal da interface grafica do sistema de precificacao.

Exibe o painel de navegacao com botoes para cada funcionalidade
e abre as janelas filhas correspondentes.
"""

import tkinter as tk
from tkinter import ttk

COR_AZUL       = "#1F4E79"
COR_AZUL_MED   = "#2E75B6"
COR_AZUL_CLARO = "#D6E4F0"
COR_CINZA      = "#F2F2F2"
COR_BRANCO     = "#FFFFFF"
COR_TEXTO      = "#1A1A1A"
FONTE          = ("Segoe UI", 10)
FONTE_TITULO   = ("Segoe UI", 13, "bold")


class JanelaPrincipal(tk.Tk):
    """
    Janela principal do sistema.

    Exibe cabecalho institucional, botoes de navegacao para cada
    funcionalidade e barra de status na parte inferior.
    """

    def __init__(self):
        super().__init__()
        self.title("Sistema de Precificação de Produtos Importados")
        self.resizable(True, True)
        self.configure(bg=COR_CINZA)
        self.minsize(520, 480)

        self._construir_layout()
        self.update_idletasks()
        self._centralizar()

    def _centralizar(self):
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    def _construir_layout(self):
        self._construir_cabecalho()
        self._construir_nav()
        self._construir_rodape()

    def _construir_cabecalho(self):
        """Cabecalho azul com titulo e subtitulo."""
        cab = tk.Frame(self, bg=COR_AZUL)
        cab.pack(fill="x")

        tk.Label(cab,
                 text="Sistema de Precificação",
                 font=("Segoe UI", 18, "bold"),
                 bg=COR_AZUL, fg=COR_BRANCO,
                 pady=10).pack(pady=(16, 2))

        tk.Label(cab,
                 text="Produtos Importados — Cálculo de Custos e Impostos",
                 font=("Segoe UI", 10),
                 bg=COR_AZUL, fg="#A8C7E8",
                 pady=4).pack(pady=(0, 16))

    def _construir_nav(self):
        """Grade central de botoes de navegacao."""
        frame = tk.Frame(self, bg=COR_CINZA)
        frame.pack(fill="both", expand=True, padx=40, pady=30)

        botoes = [
            ("Novo Cálculo",        "Calcula impostos e preço de venda\nde um produto importado",
             self._abrir_calcular,  "📦"),
            ("Produtos Cadastrados","Lista, busca e remove\nprodutos já calculados",
             self._abrir_produtos,  "📋"),
            ("Gráficos",            "Visualiza composição de custos,\ncomparativos e análises",
             self._abrir_graficos,  "📊"),
        ]

        for i, (titulo, descricao, comando, icone) in enumerate(botoes):
            self._cartao(frame, titulo, descricao, comando, icone, i)

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

    def _cartao(self, parent, titulo, descricao, comando, icone, col):
        """Cria um cartao de navegacao."""
        card = tk.Frame(parent, bg=COR_BRANCO, relief="flat",
                        cursor="hand2", bd=0,
                        highlightthickness=2,
                        highlightbackground=COR_AZUL_CLARO,
                        highlightcolor=COR_AZUL_MED)
        card.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")

        # Hover
        def on_enter(e):
            card.configure(highlightbackground=COR_AZUL_MED)
            lbl_titulo.configure(fg=COR_AZUL_MED)
        def on_leave(e):
            card.configure(highlightbackground=COR_AZUL_CLARO)
            lbl_titulo.configure(fg=COR_AZUL)
        for widget in [card]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", lambda e, c=comando: c())

        # Botão fixo na parte inferior — garante alinhamento entre cartões
        btn = tk.Button(card, text="Abrir",
                        font=("Segoe UI", 9, "bold"),
                        bg=COR_AZUL, fg=COR_BRANCO,
                        activebackground=COR_AZUL_MED,
                        activeforeground=COR_BRANCO,
                        relief="flat", cursor="hand2",
                        padx=20, pady=6,
                        command=comando)
        btn.pack(side="bottom", pady=(0, 16))

        # Conteúdo acima do botão
        tk.Label(card, text=icone,
                 font=("Segoe UI", 28),
                 bg=COR_BRANCO, pady=16
                 ).pack()

        lbl_titulo = tk.Label(card, text=titulo,
                               font=("Segoe UI", 12, "bold"),
                               bg=COR_BRANCO, fg=COR_AZUL)
        lbl_titulo.pack()

        tk.Label(card, text=descricao,
                 font=("Segoe UI", 9),
                 bg=COR_BRANCO, fg="#666666",
                 justify="center", pady=8,
                 wraplength=160).pack(padx=12, pady=(4, 8))

    def _construir_rodape(self):
        """Barra de status na parte inferior."""
        rodape = tk.Frame(self, bg=COR_AZUL, height=28)
        rodape.pack(fill="x", side="bottom")
        rodape.pack_propagate(False)

        self._var_status = tk.StringVar(
            value="Sistema pronto.  |  UFSCar Sorocaba — Engenharia de Produção"
        )
        tk.Label(rodape,
                 textvariable=self._var_status,
                 font=("Segoe UI", 8),
                 bg=COR_AZUL, fg="#A8C7E8"
                 ).pack(side="left", padx=12, pady=4)

    # -----------------------------------------------------------------------
    # Acoes de navegação
    # -----------------------------------------------------------------------

    def _abrir_calcular(self):
        from interfaces.janelas.calcular import JanelaCalcular
        JanelaCalcular(self)

    def _abrir_produtos(self):
        from interfaces.janelas.produtos import JanelaProdutos
        JanelaProdutos(self)

    def _abrir_graficos(self):
        from interfaces.janelas.graficos import JanelaGraficos
        JanelaGraficos(self)


def menu():
    """Ponto de entrada da interface grafica."""
    app = JanelaPrincipal()
    app.mainloop()