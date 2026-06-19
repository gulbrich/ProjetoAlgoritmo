"""
graficos.py
-----------
Janela de visualizacao de graficos embutidos via matplotlib + tkinter.

Os graficos sao renderizados dentro da propria janela usando
FigureCanvasTkAgg, sem abrir janelas externas do matplotlib.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from modulos.controller import calcular_produto, consultar_produtos, consultar_por_id
from modulos.graficos import composicao_custo, comparativo_produtos, comparativo_estados

COR_AZUL     = "#1F4E79"
COR_AZUL_MED = "#2E75B6"
COR_CINZA    = "#F2F2F2"
COR_BRANCO   = "#FFFFFF"
COR_TEXTO    = "#1A1A1A"
FONTE        = ("Segoe UI", 10)
FONTE_TITULO = ("Segoe UI", 12, "bold")
FONTE_SECAO  = ("Segoe UI", 10, "bold")



def _categoria_do_produto(produto: dict) -> dict:
    """
    Reconstrói o dicionário de categoria a partir de um produto salvo.

    Usa categoria_dados se disponível (produtos salvos após a correção).
    Caso contrário, busca pelo nome da categoria no arquivo JSON.
    """
    # Produtos salvos recentemente já têm o dicionário completo
    if "categoria_dados" in produto:
        return produto["categoria_dados"]
    # Produtos salvos antes da correção: busca pelo nome
    from modulos.categorias import obter_categoria
    try:
        return obter_categoria(produto["categoria"])
    except (ValueError, KeyError):
        return {
            "descricao"   : produto.get("categoria", "—"),
            "aliquota_ii" : 0.0,
            "aliquota_ipi": 0.0,
        }


class JanelaGraficos(tk.Toplevel):
    """
    Janela de graficos embutidos.

    Permite escolher o tipo de grafico e os produtos a visualizar.
    O grafico e renderizado inline via FigureCanvasTkAgg.

    Parametros:
        parent           : janela pai
        resultado_inicial: se fornecido, pre-seleciona e exibe o grafico
                           de composicao deste resultado imediatamente
    """

    def __init__(self, parent, resultado_inicial: dict = None):
        super().__init__(parent)
        self.title("Gráficos")
        self.resizable(True, True)
        self.configure(bg=COR_CINZA)
        self.withdraw()  # oculta até estar pronta para exibir

        self._resultado_inicial = resultado_inicial
        self._canvas_widget     = None
        self._toolbar_widget    = None
        self._fig               = None

        self._construir_layout()
        self.after(50, self._exibir_centralizada)

    def _exibir_centralizada(self):
        """Centraliza e exibe a janela após renderização."""
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"900x680+{(sw - 900) // 2}+{(sh - 680) // 2}")
        self.deiconify()
        self.grab_set()
        if self._resultado_inicial:
            self._tipo_var.set("Composição do custo")
            self._atualizar_painel()
            self._gerar_composicao_direta(self._resultado_inicial)

    def _construir_layout(self):
        # Cabecalho
        cab = tk.Frame(self, bg=COR_AZUL)
        cab.pack(fill="x")
        tk.Label(cab, text="Gráficos",
                 font=("Segoe UI", 14, "bold"),
                 bg=COR_AZUL, fg=COR_BRANCO, pady=12
                 ).pack(side="left", padx=16)

        # Painel de controles
        ctrl = tk.Frame(self, bg=COR_CINZA)
        ctrl.pack(fill="x", padx=16, pady=10)

        tk.Label(ctrl, text="Tipo de gráfico:", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO).pack(side="left")

        self._tipo_var = tk.StringVar()
        tipos = [
            "Composição do custo",
            "Comparativo entre produtos",
            "Comparativo por estado",
        ]
        cb = ttk.Combobox(ctrl, textvariable=self._tipo_var,
                          values=tipos, state="readonly",
                          width=28, font=FONTE)
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda _: self._atualizar_painel())

        # Painel dinâmico de parametros
        self._frame_params = tk.Frame(self, bg=COR_CINZA)
        self._frame_params.pack(fill="x", padx=16, pady=(0, 8))

        # Area do gráfico
        self._frame_grafico = tk.Frame(self, bg=COR_BRANCO, relief="solid", bd=1)
        self._frame_grafico.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        tk.Label(self._frame_grafico,
                 text="Selecione um tipo de gráfico e clique em Gerar.",
                 font=FONTE, bg=COR_BRANCO, fg="#888888"
                 ).pack(expand=True)

        # Rodape
        rodape = tk.Frame(self, bg=COR_CINZA)
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ttk.Button(rodape, text="Fechar",
                   command=self.destroy).pack(side="right")
        ttk.Button(rodape, text="Salvar imagem",
                   command=self._salvar_imagem).pack(side="right", padx=8)

    # -----------------------------------------------------------------------
    # Painel de parametros dinâmico
    # -----------------------------------------------------------------------

    def _atualizar_painel(self):
        """Reconstroi o painel de parametros conforme o tipo selecionado."""
        for w in self._frame_params.winfo_children():
            w.destroy()

        tipo = self._tipo_var.get()
        produtos = consultar_produtos()

        if tipo == "Composição do custo":
            self._painel_composicao(produtos)
        elif tipo == "Comparativo entre produtos":
            self._painel_comparativo(produtos)
        elif tipo == "Comparativo por estado":
            self._painel_estados(produtos)

    def _painel_composicao(self, produtos: list):
        """Painel de selecao de produto para grafico de composicao."""
        frame = self._frame_params
        tk.Label(frame, text="Produto:", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO).pack(side="left")

        self._var_prod_comp = tk.StringVar()
        opcoes = [f"{p['id']} — {p['nome']}" for p in produtos]
        if not opcoes:
            opcoes = ["Nenhum produto cadastrado"]

        ttk.Combobox(frame, textvariable=self._var_prod_comp,
                     values=opcoes, state="readonly",
                     width=36, font=FONTE).pack(side="left", padx=8)

        if self._resultado_inicial:
            pass  # será pré-gerado diretamente
        else:
            ttk.Button(frame, text="Gerar",
                       command=self._gerar_composicao).pack(side="left")

    def _painel_comparativo(self, produtos: list):
        """Painel de selecao multipla para grafico comparativo."""
        frame = self._frame_params
        tk.Label(frame, text="Selecione 2 ou mais produtos (Ctrl+clique):",
                 font=FONTE, bg=COR_CINZA, fg=COR_TEXTO).pack(anchor="w")

        frame_lista = tk.Frame(frame, bg=COR_CINZA)
        frame_lista.pack(fill="x", pady=4)

        self._listbox_comp = tk.Listbox(frame_lista, selectmode="multiple",
                                        font=FONTE, height=5, width=50,
                                        exportselection=False)
        for p in produtos:
            self._listbox_comp.insert("end",
                f"{p['id']} — {p['nome']} ({p['categoria']})")
        self._listbox_comp.pack(side="left")

        ttk.Button(frame_lista, text="Gerar",
                   command=self._gerar_comparativo).pack(side="left", padx=8, anchor="n")

    def _painel_estados(self, produtos: list):
        """Painel de selecao de produto e estados para comparativo."""
        frame = self._frame_params

        linha1 = tk.Frame(frame, bg=COR_CINZA)
        linha1.pack(fill="x", pady=2)
        tk.Label(linha1, text="Produto:", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, width=10).pack(side="left")
        self._var_prod_est = tk.StringVar()
        opcoes = [f"{p['id']} — {p['nome']}" for p in produtos]
        if not opcoes:
            opcoes = ["Nenhum produto cadastrado"]
        ttk.Combobox(linha1, textvariable=self._var_prod_est,
                     values=opcoes, state="readonly",
                     width=36, font=FONTE).pack(side="left", padx=8)

        linha2 = tk.Frame(frame, bg=COR_CINZA)
        linha2.pack(fill="x", pady=2)
        tk.Label(linha2, text="Estados:", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, width=10).pack(side="left")
        self._var_estados = tk.StringVar(value="SP, MG, BA, RS, PR")
        ttk.Entry(linha2, textvariable=self._var_estados,
                  width=40, font=FONTE).pack(side="left", padx=8)
        tk.Label(linha2, text="(separados por vírgula)",
                 font=("Segoe UI", 9), bg=COR_CINZA,
                 fg="#888888").pack(side="left")

        ttk.Button(frame, text="Gerar",
                   command=self._gerar_estados).pack(anchor="w", pady=4)

    # -----------------------------------------------------------------------
    # Geracao dos gráficos
    # -----------------------------------------------------------------------

    def _limpar_grafico(self):
        """Remove o grafico anterior do frame."""
        for w in self._frame_grafico.winfo_children():
            w.destroy()
        if self._fig:
            plt.close(self._fig)
            self._fig = None

    def _embutir_figura(self, fig):
        """Embute uma figura matplotlib no frame de grafico."""
        self._limpar_grafico()
        self._fig = fig

        canvas = FigureCanvasTkAgg(fig, master=self._frame_grafico)
        canvas.draw()

        toolbar = NavigationToolbar2Tk(canvas, self._frame_grafico,
                                       pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _gerar_composicao_direta(self, resultado: dict):
        """Gera grafico de composicao para um resultado ja calculado."""
        self._limpar_grafico()
        fig, ax = plt.subplots(figsize=(7, 5))
        composicao_custo(resultado, _ax=ax)
        fig.tight_layout()
        self._embutir_figura(fig)

    def _gerar_composicao(self):
        """Gera grafico de composicao para o produto selecionado."""
        sel = self._var_prod_comp.get()
        if not sel or "Nenhum" in sel:
            messagebox.showinfo("Aviso", "Selecione um produto.", parent=self)
            return
        id_produto = sel.split(" — ")[0].strip()
        try:
            produto = consultar_por_id(id_produto)
            imp = produto["impostos"]
            resultado = {
                "entrada"      : produto["entrada"],
                "cotacao"      : produto["cotacao"],
                "fonte_cotacao": produto["fonte_cotacao"],
                "categoria"    : _categoria_do_produto(produto if "produto" in dir() else p),
                "aliquota_icms": imp["icms"] / imp["valor_aduaneiro"],
                "impostos"     : imp,
                "precificacao" : produto["precificacao"],
            }
            self._gerar_composicao_direta(resultado)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)

    def _gerar_comparativo(self):
        """Gera grafico comparativo para os produtos selecionados."""
        indices = self._listbox_comp.curselection()
        if len(indices) < 2:
            messagebox.showinfo("Aviso",
                                "Selecione ao menos 2 produtos.", parent=self)
            return
        produtos = consultar_produtos()
        try:
            resultados = []
            for i in indices:
                p = produtos[i]
                imp = p["impostos"]
                resultados.append({
                    "entrada"      : p["entrada"],
                    "cotacao"      : p["cotacao"],
                    "fonte_cotacao": p["fonte_cotacao"],
                    "categoria"    : _categoria_do_produto(p),
                    "aliquota_icms": imp["icms"] / imp["valor_aduaneiro"],
                    "impostos"     : imp,
                    "precificacao" : p["precificacao"],
                })
            self._limpar_grafico()
            fig, ax = plt.subplots(figsize=(max(6, len(resultados) * 2), 5))
            comparativo_produtos(resultados, _ax=ax)
            fig.tight_layout()
            self._embutir_figura(fig)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)

    def _gerar_estados(self):
        """Gera grafico comparativo por estado."""
        sel = self._var_prod_est.get()
        if not sel or "Nenhum" in sel:
            messagebox.showinfo("Aviso", "Selecione um produto.", parent=self)
            return
        estados_str = self._var_estados.get().strip()
        if not estados_str:
            messagebox.showinfo("Aviso", "Informe ao menos um estado.", parent=self)
            return
        estados = [uf.strip().upper() for uf in estados_str.split(",") if uf.strip()]
        id_produto = sel.split(" — ")[0].strip()
        try:
            produto = consultar_por_id(id_produto)
            imp = produto["impostos"]
            resultado_base = {
                "entrada"      : produto["entrada"],
                "cotacao"      : produto["cotacao"],
                "fonte_cotacao": produto["fonte_cotacao"],
                "categoria"    : _categoria_do_produto(produto if "produto" in dir() else p),
                "aliquota_icms": imp["icms"] / imp["valor_aduaneiro"],
                "impostos"     : imp,
                "precificacao" : produto["precificacao"],
            }
            self._limpar_grafico()
            fig, ax = plt.subplots(figsize=(max(6, len(estados) * 1.2), 5))
            comparativo_estados(resultado_base, estados, calcular_produto, _ax=ax)
            fig.tight_layout()
            self._embutir_figura(fig)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self)

    def _salvar_imagem(self):
        """Salva o grafico atual como arquivo PNG."""
        if self._fig is None:
            messagebox.showinfo("Aviso", "Nenhum gráfico gerado.", parent=self)
            return
        from tkinter.filedialog import asksaveasfilename
        caminho = asksaveasfilename(
            parent=self,
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("PDF", "*.pdf")],
            title="Salvar gráfico",
        )
        if caminho:
            self._fig.savefig(caminho, bbox_inches="tight", dpi=150)
            messagebox.showinfo("Salvo", f"Gráfico salvo em:\n{caminho}", parent=self)