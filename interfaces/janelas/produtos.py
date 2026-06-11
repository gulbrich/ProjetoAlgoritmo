"""
produtos.py
-----------
Janela de listagem, busca e remocao de produtos cadastrados.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from modulos.controller import consultar_produtos, consultar_por_id, excluir_produto

COR_AZUL     = "#1F4E79"
COR_AZUL_MED = "#2E75B6"
COR_CINZA    = "#F2F2F2"
COR_BRANCO   = "#FFFFFF"
COR_TEXTO    = "#1A1A1A"
FONTE        = ("Segoe UI", 10)
FONTE_TITULO = ("Segoe UI", 12, "bold")
FONTE_SECAO  = ("Segoe UI", 10, "bold")


class JanelaProdutos(tk.Toplevel):
    """
    Janela de gerenciamento de produtos cadastrados.

    Exibe tabela com todos os produtos, permite busca por nome,
    visualizacao de detalhes e remocao.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Produtos Cadastrados")
        self.resizable(True, True)
        self.configure(bg=COR_CINZA)
        self.grab_set()

        self._construir_layout()
        self._carregar_produtos()
        self.update_idletasks()
        self._centralizar()

    def _centralizar(self):
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    def _construir_layout(self):
        # Cabecalho
        cab = tk.Frame(self, bg=COR_AZUL)
        cab.pack(fill="x")
        tk.Label(cab, text="Produtos Cadastrados",
                 font=("Segoe UI", 14, "bold"),
                 bg=COR_AZUL, fg=COR_BRANCO, pady=12
                 ).pack(side="left", padx=16)

        # Barra de busca
        barra = tk.Frame(self, bg=COR_CINZA)
        barra.pack(fill="x", padx=16, pady=10)
        tk.Label(barra, text="Buscar por nome:", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO).pack(side="left")
        self._var_busca = tk.StringVar()
        self._var_busca.trace_add("write", lambda *_: self._filtrar())
        ttk.Entry(barra, textvariable=self._var_busca,
                  width=30, font=FONTE).pack(side="left", padx=8)
        ttk.Button(barra, text="Limpar",
                   command=lambda: self._var_busca.set("")
                   ).pack(side="left")
        ttk.Button(barra, text="Atualizar",
                   command=self._carregar_produtos
                   ).pack(side="right")

        # Tabela
        frame_tab = tk.Frame(self, bg=COR_CINZA)
        frame_tab.pack(fill="both", expand=True, padx=16)

        colunas = ("id", "nome", "categoria", "uf", "preco", "margem", "data")
        self._tree = ttk.Treeview(frame_tab, columns=colunas,
                                  show="headings", selectmode="browse")

        cabecalhos = {
            "id"       : ("ID",               60),
            "nome"     : ("Nome do Produto",  200),
            "categoria": ("Categoria",        140),
            "uf"       : ("Origem→Destino",    100),
            "preco"    : ("Preço de Venda",   120),
            "margem"   : ("Margem",            70),
            "data"     : ("Data Cadastro",    140),
        }
        for col, (titulo, largura) in cabecalhos.items():
            self._tree.heading(col, text=titulo,
                               command=lambda c=col: self._ordenar(c))
            self._tree.column(col, width=largura, anchor="center")

        scroll_y = ttk.Scrollbar(frame_tab, orient="vertical",
                                 command=self._tree.yview)
        scroll_x = ttk.Scrollbar(frame_tab, orient="horizontal",
                                 command=self._tree.xview)
        self._tree.configure(yscrollcommand=scroll_y.set,
                             xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self._tree.pack(fill="both", expand=True)
        self._tree.bind("<Double-1>", lambda _: self._ver_detalhes())

        # Rodape com acoes
        rodape = tk.Frame(self, bg=COR_CINZA)
        rodape.pack(fill="x", padx=16, pady=10)
        ttk.Button(rodape, text="Ver detalhes",
                   command=self._ver_detalhes).pack(side="left", padx=(0, 8))
        ttk.Button(rodape, text="Remover produto",
                   command=self._remover).pack(side="left")
        ttk.Button(rodape, text="Fechar",
                   command=self.destroy).pack(side="right")

        # Label de contagem
        self._var_contagem = tk.StringVar()
        tk.Label(rodape, textvariable=self._var_contagem, font=FONTE,
                 bg=COR_CINZA, fg=COR_AZUL_MED).pack(side="right", padx=8)

        self._produtos = []
        self._ordem_col = None
        self._ordem_inv = False

    def _carregar_produtos(self):
        """Recarrega a lista de produtos do repositorio."""
        self._produtos = consultar_produtos()
        self._filtrar()

    def _filtrar(self):
        """Filtra a tabela pelo termo de busca."""
        termo = self._var_busca.get().strip().lower()
        for item in self._tree.get_children():
            self._tree.delete(item)

        filtrados = [p for p in self._produtos
                     if termo in p["nome"].lower()] if termo else self._produtos

        for p in filtrados:
            self._tree.insert("", "end", iid=p["id"], values=(
                p["id"],
                p["nome"],
                p["categoria"],
                f"{p['uf_origem']}→{p['uf_destino']}",
                f"R$ {p['precificacao']['preco_venda']:,.2f}",
                f"{p['precificacao']['margem_percentual']:.1f}%",
                p["data_cadastro"][:16],
            ))

        total = len(filtrados)
        self._var_contagem.set(f"{total} produto{'s' if total != 1 else ''}")

    def _ordenar(self, coluna: str):
        """Ordena a tabela pela coluna clicada."""
        if self._ordem_col == coluna:
            self._ordem_inv = not self._ordem_inv
        else:
            self._ordem_col = coluna
            self._ordem_inv = False

        idx = ["id","nome","categoria","uf","preco","margem","data"].index(coluna)
        itens = [(self._tree.set(i, coluna), i)
                 for i in self._tree.get_children()]
        itens.sort(reverse=self._ordem_inv)
        for pos, (_, item) in enumerate(itens):
            self._tree.move(item, "", pos)

    def _ver_detalhes(self):
        """Abre janela de detalhes para o produto selecionado."""
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Seleção", "Selecione um produto.", parent=self)
            return
        id_produto = sel[0]
        try:
            produto = consultar_por_id(id_produto)
            JanelaDetalhes(self, produto)
        except ValueError as e:
            messagebox.showerror("Erro", str(e), parent=self)

    def _remover(self):
        """Remove o produto selecionado apos confirmacao."""
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Seleção", "Selecione um produto.", parent=self)
            return
        id_produto = sel[0]
        try:
            produto = consultar_por_id(id_produto)
            confirma = messagebox.askyesno(
                "Confirmar remoção",
                f"Remover '{produto['nome']}'?\nEsta ação não pode ser desfeita.",
                parent=self
            )
            if confirma:
                excluir_produto(id_produto)
                self._carregar_produtos()
        except ValueError as e:
            messagebox.showerror("Erro", str(e), parent=self)


class JanelaDetalhes(tk.Toplevel):
    """
    Janela de detalhes de um produto cadastrado.

    Exibe todos os dados de entrada, impostos discriminados
    e resultado de precificacao.
    """

    def __init__(self, parent, produto: dict):
        super().__init__(parent)
        self.title(f"Detalhes — {produto['nome']}")
        self.resizable(True, True)
        self.configure(bg=COR_CINZA)
        self.grab_set()

        self._produto  = produto
        self._construir_layout()
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    def _construir_layout(self):
        p   = self._produto
        imp = p["impostos"]
        prec= p["precificacao"]
        ent = p["entrada"]

        cab = tk.Frame(self, bg=COR_AZUL)
        cab.pack(fill="x")
        tk.Label(cab, text=p["nome"],
                 font=("Segoe UI", 13, "bold"),
                 bg=COR_AZUL, fg=COR_BRANCO, pady=10
                 ).pack(side="left", padx=16)
        tk.Label(cab, text=f"ID {p['id']}  |  {p['data_cadastro'][:16]}",
                 font=FONTE, bg=COR_AZUL, fg="#A8C7E8"
                 ).pack(side="right", padx=16)

        frame = tk.Frame(self, bg=COR_CINZA)
        frame.pack(fill="both", expand=True, padx=16, pady=12)

        def secao(titulo):
            tk.Label(frame, text=titulo, font=FONTE_SECAO,
                     bg=COR_CINZA, fg=COR_AZUL).pack(anchor="w", pady=(10, 2))
            tk.Frame(frame, bg=COR_AZUL_MED, height=1).pack(fill="x", pady=(0, 6))

        def linha(label, valor):
            f = tk.Frame(frame, bg=COR_BRANCO)
            f.pack(fill="x", pady=1, padx=4)
            tk.Label(f, text=label, font=FONTE, bg=COR_BRANCO,
                     fg=COR_TEXTO, anchor="w", width=26).pack(side="left")
            tk.Label(f, text=valor, font=FONTE, bg=COR_BRANCO,
                     fg=COR_TEXTO, anchor="e").pack(side="right", padx=8)

        secao("Dados de Entrada")
        linha("Categoria",          p["categoria"])
        linha("UF Origem → Destino",f"{p['uf_origem']} → {p['uf_destino']}")
        linha("Valor em USD",       f"US$ {ent['valor_usd']:,.2f}")
        linha("Cotação utilizada",  f"R$ {p['cotacao']:.4f} ({p['fonte_cotacao']})")
        linha("Frete internacional",f"R$ {ent['frete']:,.2f}")
        linha("Despesas aduaneiras",f"R$ {ent['despesas']:,.2f}")
        linha("Quantidade",         f"{prec['quantidade']} unidades")
        linha("Margem desejada",    f"{prec['margem_percentual']:.1f}%")

        secao("Impostos")
        valor_produto = ent["valor_usd"] * p["cotacao"]
        linha("Valor do produto",   f"R$ {valor_produto:,.2f}")
        linha("Valor aduaneiro",    f"R$ {imp['valor_aduaneiro']:,.2f}")
        linha("II",                 f"R$ {imp['ii']:,.2f}")
        linha("IPI",                f"R$ {imp['ipi']:,.2f}")
        linha("PIS",                f"R$ {imp['pis']:,.2f}")
        linha("COFINS",             f"R$ {imp['cofins']:,.2f}")
        linha("ICMS",               f"R$ {imp['icms']:,.2f}")
        linha("Total de impostos",  f"R$ {imp['total_impostos']:,.2f}")

        secao("Precificação")
        linha("Custo unitário",     f"R$ {prec['custo_unitario']:,.2f}")
        linha("Preço de venda",     f"R$ {prec['preco_venda']:,.2f}")
        linha("Lucro unitário",     f"R$ {prec['lucro_unitario']:,.2f}")
        linha("Receita total",      f"R$ {prec['receita_total']:,.2f}")
        linha("Lucro do lote",      f"R$ {prec['lucro_total_lote']:,.2f}")

        ttk.Button(self, text="Ver gráfico de composição",
                   command=self._abrir_grafico).pack(pady=8)
        ttk.Button(self, text="Fechar",
                   command=self.destroy).pack(pady=(0, 12))

    def _abrir_grafico(self):
        from interfaces.janelas.graficos import JanelaGraficos
        p   = self._produto
        imp = p["impostos"]
        resultado = {
            "entrada"      : p["entrada"],
            "cotacao"      : p["cotacao"],
            "fonte_cotacao": p["fonte_cotacao"],
            "categoria"    : p["entrada"],
            "aliquota_icms": imp["icms"] / imp["valor_aduaneiro"],
            "impostos"     : imp,
            "precificacao" : p["precificacao"],
        }
        JanelaGraficos(self, resultado_inicial=resultado)
