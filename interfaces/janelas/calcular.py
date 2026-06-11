"""
calcular.py
-----------
Janela de novo calculo de precificacao.

Exibe formulario com todos os campos necessarios, executa o calculo
via controller e exibe o resultado na propria janela.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from modulos.controller  import calcular_produto, salvar_produto
from modulos.categorias  import listar_categorias
from modulos.icms        import listar_ufs
from modulos.cotacao     import obter_cotacao

# Paleta corporativa
COR_AZUL     = "#1F4E79"
COR_AZUL_MED = "#2E75B6"
COR_CINZA    = "#F2F2F2"
COR_BRANCO   = "#FFFFFF"
COR_TEXTO    = "#1A1A1A"
COR_VERDE    = "#375623"
COR_ERRO     = "#C00000"
FONTE        = ("Segoe UI", 10)
FONTE_TITULO = ("Segoe UI", 12, "bold")
FONTE_SECAO  = ("Segoe UI", 10, "bold")


class JanelaCalcular(tk.Toplevel):
    """
    Janela de formulario para calculo de precificacao de produto importado.

    Abre como janela filha da janela principal. Permite preencher os dados
    do produto, buscar a cotacao automaticamente e visualizar o resultado.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Novo Cálculo de Precificação")
        self.resizable(True, True)
        self.configure(bg=COR_CINZA)
        self.grab_set()  # foca nesta janela

        self._resultado = None
        self._categorias = listar_categorias()
        self._ufs = listar_ufs()

        self._construir_layout()
        self._buscar_cotacao_auto()
        self.update_idletasks()
        self._centralizar()

    def _centralizar(self):
        """Centraliza a janela na tela."""
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    def _construir_layout(self):
        """Constroi o layout completo da janela."""
        # Cabecalho
        cab = tk.Frame(self, bg=COR_AZUL)
        cab.pack(fill="x")
        tk.Label(cab, text="Novo Cálculo de Precificação",
                 font=("Segoe UI", 14, "bold"),
                 bg=COR_AZUL, fg=COR_BRANCO,
                 pady=12).pack(side="left", padx=16)

        # Canvas + scrollbar para o formulario
        container = tk.Frame(self, bg=COR_CINZA)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=COR_CINZA, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self._frame_form = tk.Frame(canvas, bg=COR_CINZA)

        self._frame_form.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._frame_form, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._construir_secao_cotacao()
        self._construir_secao_produto()
        self._construir_secao_valores()
        self._construir_botoes_acao()
        self._frame_resultado = tk.Frame(self._frame_form, bg=COR_CINZA)
        self._frame_resultado.pack(fill="x", padx=16, pady=(0, 16))

    def _secao(self, titulo: str) -> tk.Frame:
        """Cria e retorna um frame de secao com titulo."""
        frame = tk.Frame(self._frame_form, bg=COR_CINZA)
        frame.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(frame, text=titulo, font=FONTE_SECAO,
                 bg=COR_CINZA, fg=COR_AZUL).pack(anchor="w")
        sep = tk.Frame(frame, bg=COR_AZUL_MED, height=1)
        sep.pack(fill="x", pady=(2, 8))
        return frame

    def _campo(self, parent: tk.Frame, label: str, row: int,
               widget=None) -> tk.Widget:
        """Cria um campo de formulario com label e retorna o widget de entrada."""
        tk.Label(parent, text=label, font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, anchor="w",
                 width=22).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 8))
        if widget is None:
            var = tk.StringVar()
            entry = ttk.Entry(parent, textvariable=var, width=28, font=FONTE)
            entry.grid(row=row, column=1, sticky="w", pady=4)
            return entry, var
        widget.grid(row=row, column=1, sticky="w", pady=4)
        return widget

    def _construir_secao_cotacao(self):
        sec = self._secao("Cotação do Dólar")
        grid = tk.Frame(sec, bg=COR_CINZA)
        grid.pack(fill="x")

        self._var_cotacao = tk.StringVar()
        self._var_fonte   = tk.StringVar(value="—")

        tk.Label(grid, text="Cotação (R$/USD):", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, width=22, anchor="w"
                 ).grid(row=0, column=0, sticky="w", pady=4, padx=(0, 8))

        entry_cot = ttk.Entry(grid, textvariable=self._var_cotacao, width=16, font=FONTE)
        entry_cot.grid(row=0, column=1, sticky="w", pady=4)

        tk.Label(grid, textvariable=self._var_fonte, font=FONTE,
                 bg=COR_CINZA, fg=COR_AZUL_MED
                 ).grid(row=0, column=2, sticky="w", padx=8)

        ttk.Button(grid, text="Atualizar via API",
                   command=self._buscar_cotacao_auto
                   ).grid(row=0, column=3, padx=8)

    def _construir_secao_produto(self):
        sec = self._secao("Dados do Produto")
        grid = tk.Frame(sec, bg=COR_CINZA)
        grid.pack(fill="x")

        _, self._var_nome = self._campo(grid, "Nome do produto:", 0)

        # Categoria por combobox
        tk.Label(grid, text="Categoria:", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, anchor="w",
                 width=22).grid(row=1, column=0, sticky="w", pady=4, padx=(0, 8))
        self._var_categoria = tk.StringVar()
        desc_categorias = [f"{i+1}. {desc}" for i, (_, desc) in enumerate(self._categorias)]
        cb_cat = ttk.Combobox(grid, textvariable=self._var_categoria,
                              values=desc_categorias, state="readonly",
                              width=35, font=FONTE)
        cb_cat.grid(row=1, column=1, columnspan=2, sticky="w", pady=4)

        # UF origem
        tk.Label(grid, text="UF de origem:", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, anchor="w",
                 width=22).grid(row=2, column=0, sticky="w", pady=4, padx=(0, 8))
        self._var_uf_origem = tk.StringVar(value="SP")
        cb_orig = ttk.Combobox(grid, textvariable=self._var_uf_origem,
                               values=self._ufs, state="readonly",
                               width=8, font=FONTE)
        cb_orig.grid(row=2, column=1, sticky="w", pady=4)

        # UF destino
        tk.Label(grid, text="UF de destino:", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, anchor="w",
                 width=22).grid(row=3, column=0, sticky="w", pady=4, padx=(0, 8))
        self._var_uf_destino = tk.StringVar(value="SP")
        cb_dest = ttk.Combobox(grid, textvariable=self._var_uf_destino,
                               values=self._ufs, state="readonly",
                               width=8, font=FONTE)
        cb_dest.grid(row=3, column=1, sticky="w", pady=4)

    def _construir_secao_valores(self):
        sec = self._secao("Valores e Precificação")
        grid = tk.Frame(sec, bg=COR_CINZA)
        grid.pack(fill="x")

        campos = [
            ("Valor em USD (US$):",     "_var_valor_usd",  ""),
            ("Frete internacional (R$):", "_var_frete",    "0"),
            ("Despesas aduaneiras (R$):", "_var_despesas", "0"),
            ("Quantidade (unidades):",   "_var_quantidade", "1"),
            ("Margem de lucro (%):",     "_var_margem",    ""),
        ]
        for i, (label, attr, padrao) in enumerate(campos):
            var = tk.StringVar(value=padrao)
            setattr(self, attr, var)
            tk.Label(grid, text=label, font=FONTE, bg=COR_CINZA,
                     fg=COR_TEXTO, anchor="w", width=26
                     ).grid(row=i, column=0, sticky="w", pady=4, padx=(0, 8))
            ttk.Entry(grid, textvariable=var, width=16, font=FONTE
                      ).grid(row=i, column=1, sticky="w", pady=4)

    def _construir_botoes_acao(self):
        frame = tk.Frame(self._frame_form, bg=COR_CINZA)
        frame.pack(fill="x", padx=16, pady=12)

        ttk.Button(frame, text="Calcular",
                   command=self._calcular).pack(side="left", padx=(0, 8))
        ttk.Button(frame, text="Limpar",
                   command=self._limpar).pack(side="left")
        ttk.Button(frame, text="Fechar",
                   command=self.destroy).pack(side="right")

    # -----------------------------------------------------------------------
    # Acoes
    # -----------------------------------------------------------------------

    def _buscar_cotacao_auto(self):
        """Tenta buscar a cotacao via API e preenche o campo."""
        self._var_fonte.set("Buscando...")
        self.update_idletasks()
        try:
            cotacao = obter_cotacao()
            self._var_cotacao.set(f"{cotacao:.4f}")
            self._var_fonte.set("Fonte: API")
        except (ConnectionError, ValueError):
            self._var_cotacao.set("")
            self._var_fonte.set("API indisponível — informe manualmente")

    def _limpar(self):
        """Limpa todos os campos do formulario."""
        for attr in ["_var_nome", "_var_valor_usd", "_var_frete",
                     "_var_despesas", "_var_quantidade", "_var_margem"]:
            getattr(self, attr).set("")
        self._var_frete.set("0")
        self._var_despesas.set("0")
        self._var_quantidade.set("1")
        self._var_categoria.set("")
        for widget in self._frame_resultado.winfo_children():
            widget.destroy()
        self._resultado = None

    def _calcular(self):
        """Valida os campos, executa o calculo e exibe o resultado."""
        dados = self._coletar_dados()
        if dados is None:
            return
        try:
            self._resultado = calcular_produto(dados)
            self._exibir_resultado(self._resultado)
        except (ValueError, TypeError, KeyError) as e:
            messagebox.showerror("Erro no cálculo", str(e), parent=self)

    def _coletar_dados(self) -> dict | None:
        """
        Coleta e valida os campos do formulario.
        Retorna None se houver erro de validacao.
        """
        erros = []

        nome = self._var_nome.get().strip()
        if not nome:
            erros.append("Nome do produto é obrigatório.")

        if not self._var_categoria.get():
            erros.append("Selecione uma categoria.")
            idx_cat = -1
        else:
            idx_cat = int(self._var_categoria.get().split(".")[0]) - 1

        cotacao_str = self._var_cotacao.get().strip().replace(",", ".")
        try:
            cotacao = float(cotacao_str)
            if cotacao <= 0:
                raise ValueError
        except ValueError:
            erros.append("Cotação do dólar inválida.")
            cotacao = 0

        try:
            valor_usd = float(self._var_valor_usd.get().replace(",", "."))
            if valor_usd <= 0:
                raise ValueError
        except ValueError:
            erros.append("Valor em USD inválido.")
            valor_usd = 0

        try:
            frete = float(self._var_frete.get().replace(",", ".") or "0")
        except ValueError:
            erros.append("Frete inválido.")
            frete = 0

        try:
            despesas = float(self._var_despesas.get().replace(",", ".") or "0")
        except ValueError:
            erros.append("Despesas inválidas.")
            despesas = 0

        try:
            quantidade = int(self._var_quantidade.get() or "1")
            if quantidade < 1:
                raise ValueError
        except ValueError:
            erros.append("Quantidade deve ser um inteiro maior que zero.")
            quantidade = 1

        try:
            margem = float(self._var_margem.get().replace(",", ".")) / 100
            if not 0 < margem < 1:
                raise ValueError
        except ValueError:
            erros.append("Margem de lucro inválida (ex: 30 para 30%).")
            margem = 0

        if erros:
            messagebox.showerror("Campos inválidos",
                                 "\n".join(f"• {e}" for e in erros), parent=self)
            return None

        chave_cat, _ = self._categorias[idx_cat]
        return {
            "nome"      : nome,
            "categoria" : chave_cat,
            "uf_origem" : self._var_uf_origem.get(),
            "uf_destino": self._var_uf_destino.get(),
            "valor_usd" : valor_usd,
            "frete"     : frete,
            "despesas"  : despesas,
            "quantidade": quantidade,
            "margem"    : margem,
            "cotacao"   : cotacao,
        }

    def _exibir_resultado(self, resultado: dict):
        """Exibe o resultado do calculo em painel estruturado."""
        for widget in self._frame_resultado.winfo_children():
            widget.destroy()

        imp  = resultado["impostos"]
        prec = resultado["precificacao"]
        ent  = resultado["entrada"]

        # Titulo
        tk.Label(self._frame_resultado,
                 text="Resultado do Cálculo",
                 font=FONTE_TITULO, bg=COR_AZUL, fg=COR_BRANCO,
                 pady=6).pack(fill="x")

        # Duas colunas: composicao do custo | precificacao
        cols = tk.Frame(self._frame_resultado, bg=COR_CINZA)
        cols.pack(fill="x", pady=8)

        col_esq = tk.Frame(cols, bg=COR_BRANCO, relief="solid", bd=1)
        col_dir = tk.Frame(cols, bg=COR_BRANCO, relief="solid", bd=1)
        col_esq.pack(side="left", fill="both", expand=True, padx=(0, 4))
        col_dir.pack(side="left", fill="both", expand=True, padx=(4, 0))

        def titulo_col(parent, texto):
            tk.Label(parent, text=texto, font=FONTE_SECAO,
                     bg=COR_AZUL_MED, fg=COR_BRANCO,
                     pady=4).pack(fill="x")

        def linha(parent, label, valor, destaque=False):
            f = tk.Frame(parent, bg=COR_BRANCO)
            f.pack(fill="x", padx=8, pady=1)
            cor_valor = COR_AZUL if destaque else COR_TEXTO
            tk.Label(f, text=label, font=FONTE, bg=COR_BRANCO,
                     fg=COR_TEXTO, anchor="w", width=22).pack(side="left")
            tk.Label(f, text=valor, font=FONTE if not destaque else FONTE_SECAO,
                     bg=COR_BRANCO, fg=cor_valor, anchor="e").pack(side="right")

        # Coluna esquerda — composicao do custo
        titulo_col(col_esq, "Composição do Custo")
        valor_produto = ent["valor_usd"] * ent["cotacao"]
        linha(col_esq, "Valor do produto", f"R$ {valor_produto:,.2f}")
        linha(col_esq, "Frete", f"R$ {imp['valor_aduaneiro'] - valor_produto:,.2f}")
        linha(col_esq, f"II ({resultado['categoria']['aliquota_ii']*100:.0f}%)", f"R$ {imp['ii']:,.2f}")
        linha(col_esq, f"IPI ({resultado['categoria']['aliquota_ipi']*100:.0f}%)", f"R$ {imp['ipi']:,.2f}")
        linha(col_esq, "PIS (2,10%)", f"R$ {imp['pis']:,.2f}")
        linha(col_esq, "COFINS (9,65%)", f"R$ {imp['cofins']:,.2f}")
        linha(col_esq, f"ICMS ({resultado['aliquota_icms']*100:.0f}%)", f"R$ {imp['icms']:,.2f}")
        linha(col_esq, "Despesas aduaneiras", f"R$ {imp['despesas']:,.2f}")
        tk.Frame(col_esq, bg=COR_AZUL_MED, height=1).pack(fill="x", padx=8, pady=4)
        linha(col_esq, "Total de impostos", f"R$ {imp['total_impostos']:,.2f}")
        linha(col_esq, "Custo unitário", f"R$ {prec['custo_unitario']:,.2f}", destaque=True)

        # Coluna direita — precificacao
        titulo_col(col_dir, "Precificação")
        linha(col_dir, "Margem de lucro", f"{prec['margem_percentual']:.1f}%")
        linha(col_dir, "Preço de venda", f"R$ {prec['preco_venda']:,.2f}", destaque=True)
        linha(col_dir, "Lucro unitário", f"R$ {prec['lucro_unitario']:,.2f}")
        tk.Frame(col_dir, bg=COR_AZUL_MED, height=1).pack(fill="x", padx=8, pady=4)
        linha(col_dir, "Quantidade", f"{prec['quantidade']} un.")
        linha(col_dir, "Receita total", f"R$ {prec['receita_total']:,.2f}")
        linha(col_dir, "Lucro do lote", f"R$ {prec['lucro_total_lote']:,.2f}", destaque=True)
        tk.Frame(col_dir, bg=COR_CINZA, height=8).pack()
        linha(col_dir, "Cotação utilizada", f"R$ {resultado['cotacao']:.4f} ({resultado['fonte_cotacao']})")

        # Botoes pos-calculo
        frame_btn = tk.Frame(self._frame_resultado, bg=COR_CINZA)
        frame_btn.pack(pady=8)
        ttk.Button(frame_btn, text="Salvar produto",
                   command=self._salvar).pack(side="left", padx=4)
        ttk.Button(frame_btn, text="Ver gráfico de composição",
                   command=self._abrir_grafico).pack(side="left", padx=4)

    def _salvar(self):
        """Salva o produto calculado no repositorio."""
        if self._resultado is None:
            return
        try:
            salvo = salvar_produto(self._resultado["entrada"]["nome"], self._resultado)
            messagebox.showinfo("Salvo",
                                f"Produto salvo com ID {salvo['id']}.", parent=self)
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e), parent=self)

    def _abrir_grafico(self):
        """Abre a janela de grafico de composicao para o resultado atual."""
        if self._resultado is None:
            return
        from interfaces.janelas.graficos import JanelaGraficos
        JanelaGraficos(self, resultado_inicial=self._resultado)
