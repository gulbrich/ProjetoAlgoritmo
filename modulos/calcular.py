"""
calcular.py
-----------
Janela de novo calculo de precificacao.

Exibe formulario com todos os campos necessarios, executa o calculo
via controller e exibe o resultado na propria janela.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from modulos.controller  import calcular_produto, salvar_produto, consultar_por_nome
from modulos.icms        import listar_ufs
from modulos.ncm         import buscar_ncm, obter_aliquotas_ncm, buscar_aliquotas_por_codigo, TABELA_LOCAL
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
        self.resizable(False, False)
        self.configure(bg=COR_CINZA)
        self.withdraw()  # oculta até estar pronta para exibir

        self._resultado       = None
        self._ncm_selecionado = None  # dict com codigo, aliquota_ii, aliquota_ipi
        self._ufs             = listar_ufs()
        self._fonte_cotacao   = "Manual"  # atualizado ao buscar via API

        self._construir_layout()
        self.after(50, self._exibir_centralizada)

    def _exibir_centralizada(self):
        """Centraliza e exibe a janela após o tkinter calcular seu tamanho real."""
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        largura, altura = 620, 720
        self.geometry(f"{largura}x{altura}+{(sw - largura) // 2}+{(sh - altura) // 2}")
        self.deiconify()
        self.grab_set()
        self._buscar_cotacao_silenciosa()


    def _construir_layout(self):
        """Constrói o layout completo da janela."""
        # Cabeçalho fixo no topo
        cab = tk.Frame(self, bg=COR_AZUL)
        cab.pack(fill="x")
        tk.Label(cab, text="Novo Cálculo de Precificação",
                 font=("Segoe UI", 14, "bold"),
                 bg=COR_AZUL, fg=COR_BRANCO,
                 pady=12).pack(side="left", padx=16)

        # Botões fixos no rodapé — empacotados antes do scroll
        self._construir_botoes_acao()

        # Área com scroll para o formulário
        container = tk.Frame(self, bg=COR_CINZA)
        container.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(container, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        canvas = tk.Canvas(container, bg=COR_CINZA,
                           highlightthickness=0,
                           yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)

        self._frame_form = tk.Frame(canvas, bg=COR_CINZA)
        self._frame_form_id = canvas.create_window(
            (0, 0), window=self._frame_form, anchor="nw"
        )

        # Atualiza a região de scroll quando o frame muda de tamanho
        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self._frame_form.bind("<Configure>", _on_frame_configure)

        # Ajusta a largura do frame interno ao canvas
        def _on_canvas_configure(e):
            canvas.itemconfig(self._frame_form_id, width=e.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        # Scroll com roda do mouse
        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self._construir_secao_cotacao()
        self._construir_secao_produto()
        self._construir_secao_valores()

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

        self._var_cotacao = tk.StringVar()
        self._var_fonte   = tk.StringVar(value="—")

        # Grid de duas linhas: label na coluna 0, campo+botao na coluna 1
        grid = tk.Frame(sec, bg=COR_CINZA)
        grid.pack(fill="x")

        # Linha 0: label | entry + botao
        tk.Label(grid, text="Cotação (R$/USD):", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, width=22, anchor="w"
                 ).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=2)

        frame_entry = tk.Frame(grid, bg=COR_CINZA)
        frame_entry.grid(row=0, column=1, sticky="w")
        ttk.Entry(frame_entry, textvariable=self._var_cotacao,
                  width=16, font=FONTE).pack(side="left")
        ttk.Button(frame_entry, text="Atualizar via API",
                   command=self._buscar_cotacao_auto
                   ).pack(side="left", padx=12)

        # Linha 1: vazio na coluna 0 | URL alinhada com o entry na coluna 1
        tk.Label(grid, textvariable=self._var_fonte,
                 font=("Segoe UI", 8), bg=COR_CINZA,
                 fg=COR_AZUL_MED, anchor="w"
                 ).grid(row=1, column=1, sticky="w", pady=(0, 4))

    def _construir_secao_produto(self):
        sec = self._secao("Dados do Produto")
        grid = tk.Frame(sec, bg=COR_CINZA)
        grid.pack(fill="x")

        _, self._var_nome = self._campo(grid, "Nome do produto:", 0)

        # Campo de busca com filtragem em tempo real
        tk.Label(grid, text="Buscar NCM:", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, anchor="w",
                 width=22).grid(row=1, column=0, sticky="w", pady=4, padx=(0, 8))

        frame_busca = tk.Frame(grid, bg=COR_CINZA)
        frame_busca.grid(row=1, column=1, columnspan=2, sticky="w", pady=4)

        self._var_busca_ncm = tk.StringVar()
        self._entry_busca = ttk.Entry(frame_busca, textvariable=self._var_busca_ncm,
                                      width=28, font=FONTE)
        self._entry_busca.pack(side="left")
        self._var_busca_ncm.trace_add("write", lambda *_: self._filtrar_ncm())

        ttk.Button(frame_busca, text="Buscar online",
                   command=self._buscar_ncm).pack(side="left", padx=8)

        tk.Label(frame_busca, text="↑ online se não encontrar",
                 font=("Segoe UI", 8), bg=COR_CINZA,
                 fg="#888888").pack(side="left")

        # Listbox de sugestões — aparece ao digitar
        self._frame_sugestoes = tk.Frame(grid, bg=COR_BRANCO,
                                          relief="solid", bd=1)
        self._frame_sugestoes.grid(row=2, column=1, columnspan=2,
                                    sticky="w", pady=(0, 4))
        self._frame_sugestoes.grid_remove()  # oculto inicialmente

        self._listbox_ncm = tk.Listbox(self._frame_sugestoes,
                                        font=("Segoe UI", 9),
                                        height=6, width=52,
                                        activestyle="dotbox",
                                        selectmode="single",
                                        cursor="hand2")
        scroll_sug = ttk.Scrollbar(self._frame_sugestoes,
                                    orient="vertical",
                                    command=self._listbox_ncm.yview)
        self._listbox_ncm.configure(yscrollcommand=scroll_sug.set)
        scroll_sug.pack(side="right", fill="y")
        self._listbox_ncm.pack(side="left", fill="both")
        self._listbox_ncm.bind("<<ListboxSelect>>", lambda e: self._on_sugestao_selecionada())

        # Montar lista completa de NCMs para filtragem
        self._opcoes_ncm = sorted(
            [(cod, desc, ii, ipi)
             for cod, (desc, ii, ipi) in TABELA_LOCAL.items()],
            key=lambda x: x[1]
        )

        # NCM selecionado
        tk.Label(grid, text="NCM selecionado:", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, anchor="w",
                 width=22).grid(row=3, column=0, sticky="w", pady=2, padx=(0, 8))
        self._var_ncm_label = tk.StringVar(value="Nenhum NCM selecionado")
        self._lbl_ncm = tk.Label(grid, textvariable=self._var_ncm_label,
                 font=("Segoe UI", 8), bg=COR_CINZA, fg=COR_AZUL_MED,
                 anchor="w", justify="left", wraplength=380)
        self._lbl_ncm.grid(row=3, column=1, columnspan=2, sticky="w")

        # Alíquotas editáveis
        tk.Label(grid, text="Alíquota II (%):", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, anchor="w",
                 width=22).grid(row=4, column=0, sticky="w", pady=4, padx=(0, 8))
        self._var_aliq_ii = tk.StringVar(value="")
        ttk.Entry(grid, textvariable=self._var_aliq_ii,
                  width=10, font=FONTE).grid(row=4, column=1, sticky="w", pady=4)

        tk.Label(grid, text="Alíquota IPI (%):", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, anchor="w",
                 width=22).grid(row=5, column=0, sticky="w", pady=4, padx=(0, 8))
        self._var_aliq_ipi = tk.StringVar(value="")
        ttk.Entry(grid, textvariable=self._var_aliq_ipi,
                  width=10, font=FONTE).grid(row=5, column=1, sticky="w", pady=4)

        tk.Label(grid,
                 text="Preenchido automaticamente. Se vazio, consulte "
                      "www4.receita.fazenda.gov.br/simulador/",
                 font=("Segoe UI", 8), bg=COR_CINZA, fg="#888888",
                 wraplength=300, justify="left"
                 ).grid(row=6, column=1, columnspan=2, sticky="w", pady=(0, 4))

        # UF origem
        tk.Label(grid, text="UF de origem:", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, anchor="w",
                 width=22).grid(row=7, column=0, sticky="w", pady=4, padx=(0, 8))
        self._var_uf_origem = tk.StringVar(value="SP")
        ttk.Combobox(grid, textvariable=self._var_uf_origem,
                     values=self._ufs, state="readonly",
                     width=8, font=FONTE).grid(row=7, column=1, sticky="w", pady=4)

        # UF destino
        tk.Label(grid, text="UF de destino:", font=FONTE,
                 bg=COR_CINZA, fg=COR_TEXTO, anchor="w",
                 width=22).grid(row=8, column=0, sticky="w", pady=4, padx=(0, 8))
        self._var_uf_destino = tk.StringVar(value="SP")
        ttk.Combobox(grid, textvariable=self._var_uf_destino,
                     values=self._ufs, state="readonly",
                     width=8, font=FONTE).grid(row=8, column=1, sticky="w", pady=4)

    def _filtrar_ncm(self):
        """Filtra a listbox de sugestões em tempo real conforme o usuário digita."""
        termo = self._var_busca_ncm.get().strip().lower()
        self._listbox_ncm.delete(0, "end")

        if not termo:
            self._frame_sugestoes.grid_remove()
            return

        filtrados = [
            (cod, desc, ii, ipi)
            for cod, desc, ii, ipi in self._opcoes_ncm
            if termo in desc.lower() or termo in cod.lower()
        ]

        if filtrados:
            for cod, desc, ii, ipi in filtrados:
                self._listbox_ncm.insert("end", cod + "  —  " + desc)
            self._frame_sugestoes.grid()
        else:
            self._frame_sugestoes.grid_remove()

    def _on_sugestao_selecionada(self):
        """Preenche alíquotas ao clicar numa sugestão da listbox."""
        sel = self._listbox_ncm.curselection()
        if not sel:
            return
        texto = self._listbox_ncm.get(sel[0])
        codigo = texto.split("  —  ")[0].strip()

        try:
            dados = obter_aliquotas_ncm(codigo)
        except (ValueError, ConnectionError):
            dados = None

        if dados:
            self._ncm_selecionado = {
                "codigo"      : codigo,
                "descricao"   : dados.get("descricao", ""),
                "aliquota_ii" : dados["aliquota_ii"],
                "aliquota_ipi": dados["aliquota_ipi"],
            }
            self._var_ncm_label.set(codigo + " — " + dados.get("descricao", ""))
            self._var_aliq_ii.set(str(round(dados["aliquota_ii"] * 100, 1)))
            self._var_aliq_ipi.set(str(round(dados["aliquota_ipi"] * 100, 1)))

        # Ocultar sugestões e limpar campo de busca
        self._frame_sugestoes.grid_remove()
        self._var_busca_ncm.set("")

    def _buscar_ncm(self):
        """Busca NCMs pelo termo digitado e abre janela de seleção."""
        termo = self._var_busca_ncm.get().strip()
        if not termo:
            messagebox.showwarning("Aviso", "Digite um termo para buscar.", parent=self)
            return
        try:
            resultados = buscar_ncm(termo)
        except Exception as e:
            messagebox.showerror("Erro na busca", str(e), parent=self)
            return
        if not resultados:
            messagebox.showinfo("Sem resultados",
                                "Nenhum NCM encontrado para: " + termo,
                                parent=self)
            return
        JanelaSelecionarNCM(self, resultados, self._on_ncm_selecionado)

    def _on_ncm_selecionado(self, ncm: dict):
        """Callback chamado quando o usuário seleciona um NCM."""
        self._ncm_selecionado = ncm
        codigo    = ncm["codigo"]
        descricao = ncm["descricao"]
        self._var_ncm_label.set(codigo + " — " + descricao)

        # Limpa os campos antes de buscar
        self._var_aliq_ii.set("Buscando...")
        self._var_aliq_ipi.set("Buscando...")
        self.update_idletasks()

        # Busca as alíquotas pelo código específico na API
        try:
            # Tenta tabela local primeiro (mais rápido)
            dados = obter_aliquotas_ncm(codigo)
        except (ValueError, ConnectionError):
            try:
                # Tenta BrasilAPI pelo código específico
                dados = buscar_aliquotas_por_codigo(codigo)
            except (ValueError, ConnectionError):
                dados = None

        if dados:
            ii  = dados["aliquota_ii"]
            ipi = dados["aliquota_ipi"]
            self._var_aliq_ii.set(str(round(ii * 100, 1)))
            self._var_aliq_ipi.set(str(round(ipi * 100, 1)))
            self._ncm_selecionado = {**ncm, **dados}
            if ipi == 0.0 and dados.get("fonte", "") == "BrasilAPI":
                msg = ("IPI retornado como 0% pela API — pode estar incorreto. "
                       "Verifique em: www4.receita.fazenda.gov.br/simulador/")
                messagebox.showwarning("IPI nao confirmado", msg, parent=self)
        else:
            self._var_aliq_ii.set("")
            self._var_aliq_ipi.set("")
            msg = ("Nao foi possivel obter as aliquotas para este NCM. "
                   "Informe II e IPI manualmente. "
                   "Consulte: www4.receita.fazenda.gov.br/simulador/")
            messagebox.showwarning("Aliquotas nao encontradas", msg, parent=self)

    def _subcampo(self, grid, label, attr, padrao, row, descricao=None):
        """Cria um campo de entrada com label e descrição opcional abaixo do entry."""
        var = tk.StringVar(value=padrao)
        setattr(self, attr, var)

        # Cada subcampo ocupa duas linhas no grid: campo na linha par, descrição na ímpar
        linha_campo = row * 2
        linha_desc  = row * 2 + 1

        tk.Label(grid, text=label, font=FONTE, bg=COR_BRANCO,
                 fg=COR_TEXTO, anchor="w", width=26
                 ).grid(row=linha_campo, column=0, sticky="w", pady=(4, 0), padx=(8, 8))
        ttk.Entry(grid, textvariable=var, width=16, font=FONTE
                  ).grid(row=linha_campo, column=1, sticky="w", pady=(4, 0))
        if descricao:
            tk.Label(grid, text=descricao, font=("Segoe UI", 8),
                     bg=COR_BRANCO, fg="#888888", anchor="w"
                     ).grid(row=linha_desc, column=1, sticky="w", padx=(0, 8), pady=(0, 4))

    def _construir_secao_valores(self):
        sec = self._secao("Valores e Precificação")

        def subsecao(parent, titulo):
            """Cria uma subsecao com fundo branco e titulo em negrito."""
            tk.Label(parent, text=titulo, font=("Segoe UI", 9, "bold"),
                     bg=COR_CINZA, fg=COR_AZUL_MED, anchor="w"
                     ).pack(anchor="w", pady=(6, 2))
            frame = tk.Frame(parent, bg=COR_BRANCO, relief="solid", bd=1)
            frame.pack(fill="x", pady=(0, 4))
            return frame

        # --- Por unidade ---
        grid_unit = subsecao(sec, "Por unidade")
        self._subcampo(grid_unit, "Valor em USD (US$):", "_var_valor_usd", "",
                       row=0, descricao="Preço pago ao fornecedor por unidade")
        self._subcampo(grid_unit, "Margem de lucro (%):", "_var_margem", "",
                       row=1, descricao="Ex: 30 para 30% sobre o preço de venda")

        # --- Por lote ---
        grid_lote = subsecao(sec, "Por lote")
        self._subcampo(grid_lote, "Quantidade (unidades):", "_var_quantidade", "1",
                       row=0, descricao="Total de unidades adquiridas")
        self._subcampo(grid_lote, "Frete internacional (R$):", "_var_frete", "0",
                       row=1, descricao="Custo total de transporte até o Brasil")
        self._subcampo(grid_lote, "Outras despesas (R$):", "_var_despesas", "0",
                       row=2, descricao="SISCOMEX, despachante, armazenagem, etc.")

    def _construir_botoes_acao(self):
        """Botoes fixos no rodapé da janela, sempre visíveis."""
        frame = tk.Frame(self, bg=COR_CINZA)
        frame.pack(fill="x", padx=16, pady=10, side="bottom")
        sep = tk.Frame(self, bg=COR_AZUL_MED, height=1)
        sep.pack(fill="x", side="bottom")

        ttk.Button(frame, text="Calcular",
                   command=self._calcular).pack(side="left", padx=(0, 8))
        ttk.Button(frame, text="Limpar",
                   command=self._limpar).pack(side="left")
        ttk.Button(frame, text="Fechar",
                   command=self.destroy).pack(side="right")

    # -----------------------------------------------------------------------
    # Acoes
    # -----------------------------------------------------------------------

    def _buscar_cotacao_silenciosa(self):
        """Busca a cotacao ao abrir a janela, sem exibir messagebox."""
        self._var_fonte.set("Buscando...")
        self.update_idletasks()
        try:
            cotacao = obter_cotacao()
            self._var_cotacao.set(f"{cotacao:.4f}")
            self._var_fonte.set("economia.awesomeapi.com.br")
            self._fonte_cotacao = "API"
        except (ConnectionError, ValueError):
            self._var_cotacao.set("")
            self._var_fonte.set("Informe manualmente")
            self._fonte_cotacao = "Manual"

    def _buscar_cotacao_auto(self):
        """Busca a cotacao ao clicar em Atualizar, exibindo messagebox."""
        self._var_fonte.set("Buscando...")
        self.update_idletasks()
        try:
            cotacao = obter_cotacao()
            self._var_cotacao.set(f"{cotacao:.4f}")
            self._var_fonte.set("economia.awesomeapi.com.br")
            self._fonte_cotacao = "API"
            messagebox.showinfo(
                "Cotação atualizada",
                f"Cotação obtida com sucesso:\n\nUS$ 1,00 = R$ {cotacao:.4f}\n\nFonte: economia.awesomeapi.com.br",
                parent=self,
            )
        except (ConnectionError, ValueError) as e:
            self._var_cotacao.set("")
            self._var_fonte.set("Informe manualmente")
            self._fonte_cotacao = "Manual"
            messagebox.showwarning(
                "Cotação indisponível",
                f"Não foi possível buscar a cotação automática:\n\n{e}\n\nInforme o valor manualmente.",
                parent=self,
            )

    def _limpar(self):
        """Limpa todos os campos do formulário."""
        for attr in ["_var_nome", "_var_valor_usd", "_var_frete",
                     "_var_despesas", "_var_quantidade", "_var_margem"]:
            getattr(self, attr).set("")
        self._var_frete.set("0")
        self._var_despesas.set("0")
        self._var_quantidade.set("1")
        self._var_busca_ncm.set("")
        self._var_ncm_label.set("Nenhum NCM selecionado")
        self._var_aliq_ii.set("")
        self._var_aliq_ipi.set("")
        self._listbox_ncm.delete(0, "end")
        self._frame_sugestoes.grid_remove()
        self._ncm_selecionado = None
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

        if not self._ncm_selecionado:
            erros.append("Busque e selecione um NCM para o produto.")

        try:
            aliq_ii = float(self._var_aliq_ii.get().replace(",", ".")) / 100
            if not 0 <= aliq_ii < 1:
                raise ValueError
        except ValueError:
            erros.append("Alíquota de II inválida (ex: 16 para 16%).")
            aliq_ii = 0

        try:
            aliq_ipi = float(self._var_aliq_ipi.get().replace(",", ".")) / 100
            if not 0 <= aliq_ipi < 1:
                raise ValueError
        except (ValueError, AttributeError):
            aliq_ipi = 0

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
            margem_str = self._var_margem.get().replace(",", ".").replace("%", "").strip()
            margem = float(margem_str) / 100
            if margem <= 0:
                raise ValueError
        except ValueError:
            erros.append("Margem de lucro invalida. Digite um numero positivo (ex: 30 para 30%, 150 para 150%).")
            margem = 0

        if erros:
            messagebox.showerror("Campos inválidos",
                                 "\n".join("• " + e for e in erros), parent=self)
            return None

        ncm = self._ncm_selecionado
        return {
            "nome"           : nome,
            "categoria"      : ncm.get("codigo", "NCM"),
            "categoria_dados": {
                "descricao"   : ncm.get("descricao", ncm.get("codigo", "")),
                "aliquota_ii" : aliq_ii,
                "aliquota_ipi": aliq_ipi,
            },
            "uf_origem"      : self._var_uf_origem.get(),
            "uf_destino"     : self._var_uf_destino.get(),
            "valor_usd"      : valor_usd,
            "frete"          : frete,
            "despesas"       : despesas,
            "quantidade"     : quantidade,
            "margem"         : margem,
            "cotacao"        : cotacao,
            "fonte_cotacao"  : self._fonte_cotacao,
        }

    def _exibir_resultado(self, resultado: dict):
        """Abre janela separada com o resultado do calculo."""
        JanelaResultado(self, resultado)




class JanelaSelecionarNCM(tk.Toplevel):
    """
    Janela de seleção de NCM a partir dos resultados de busca.

    Exibe lista de NCMs encontrados e chama o callback quando
    o usuário confirma a seleção.
    """

    def __init__(self, parent, resultados: list, callback):
        super().__init__(parent)
        self.title("Selecionar NCM")
        self.resizable(False, False)
        self.configure(bg=COR_CINZA)
        self.withdraw()

        self._resultados = resultados
        self._callback   = callback

        self._construir_layout()
        self.after(50, self._exibir_centralizada)

    def _exibir_centralizada(self):
        self.update_idletasks()
        w  = self.winfo_reqwidth()
        h  = self.winfo_reqheight()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{max(w, 600)}x{min(h+20, 500)}+{(sw-max(w,600))//2}+{(sh-min(h+20,500))//2}")
        self.deiconify()
        self.grab_set()

    def _construir_layout(self):
        cab = tk.Frame(self, bg=COR_AZUL)
        cab.pack(fill="x")
        tk.Label(cab, text="Selecione o NCM do produto",
                 font=("Segoe UI", 12, "bold"),
                 bg=COR_AZUL, fg=COR_BRANCO, pady=10
                 ).pack(side="left", padx=16)

        fonte = self._resultados[0].get("fonte", "") if self._resultados else ""
        tk.Label(cab, text="Fonte: " + fonte,
                 font=("Segoe UI", 8), bg=COR_AZUL,
                 fg="#A8C7E8").pack(side="right", padx=16)

        frame = tk.Frame(self, bg=COR_CINZA)
        frame.pack(fill="both", expand=True, padx=16, pady=10)

        scroll = ttk.Scrollbar(frame, orient="vertical")
        self._listbox = tk.Listbox(frame, font=("Segoe UI", 9),
                                   yscrollcommand=scroll.set,
                                   selectmode="single",
                                   activestyle="dotbox",
                                   height=15, width=70)
        scroll.config(command=self._listbox.yview)
        scroll.pack(side="right", fill="y")
        self._listbox.pack(fill="both", expand=True)
        self._listbox.bind("<Double-1>", lambda e: self._confirmar())

        for r in self._resultados:
            self._listbox.insert("end", r["codigo"] + "  —  " + r["descricao"])

        rodape = tk.Frame(self, bg=COR_CINZA)
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ttk.Button(rodape, text="Selecionar",
                   command=self._confirmar).pack(side="left", padx=(0, 8))
        ttk.Button(rodape, text="Cancelar",
                   command=self.destroy).pack(side="left")

    def _confirmar(self):
        """Confirma a seleção e chama o callback com o NCM escolhido."""
        sel = self._listbox.curselection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um NCM.", parent=self)
            return
        ncm = self._resultados[sel[0]]
        self.destroy()
        self._callback(ncm)


class JanelaResultado(tk.Toplevel):
    """
    Janela de resultado do calculo de precificacao.

    Abre após o calculo, exibindo composicao de custos e precificacao
    em duas colunas, com botoes de salvar e grafico sempre visiveis.
    """

    def __init__(self, parent, resultado: dict):
        super().__init__(parent)
        self.title("Resultado do Cálculo")
        self.resizable(False, False)
        self.configure(bg=COR_CINZA)
        self.withdraw()  # oculta até estar pronta para exibir

        self._resultado = resultado
        self._ja_salvo  = self._verificar_duplicata()
        self._construir_layout()
        self.after(50, self._exibir_centralizada_resultado)

    def _exibir_centralizada_resultado(self):
        """Centraliza e exibe a janela de resultado após renderização."""
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        largura, altura = 680, 560
        self.geometry(f"{largura}x{altura}+{(sw - largura) // 2}+{(sh - altura) // 2}")
        self.deiconify()
        self.grab_set()

    def _verificar_duplicata(self) -> bool:
        """
        Verifica se ja existe produto com o mesmo nome cadastrado.
        Retorna True se duplicata encontrada.
        """
        nome = self._resultado["entrada"]["nome"]
        return len(consultar_por_nome(nome)) > 0

    def _construir_layout(self):
        resultado = self._resultado
        imp  = resultado["impostos"]
        prec = resultado["precificacao"]
        ent  = resultado["entrada"]

        # Cabecalho
        cab = tk.Frame(self, bg=COR_AZUL)
        cab.pack(fill="x")
        tk.Label(cab, text=f"Resultado — {ent['nome']}",
                 font=("Segoe UI", 13, "bold"),
                 bg=COR_AZUL, fg=COR_BRANCO, pady=10
                 ).pack(side="left", padx=16)
        tk.Label(cab, text=f"Cotação: R$ {resultado['cotacao']:.4f} ({resultado['fonte_cotacao']})",
                 font=FONTE, bg=COR_AZUL, fg="#A8C7E8"
                 ).pack(side="right", padx=16)

        # Duas colunas
        cols = tk.Frame(self, bg=COR_CINZA)
        cols.pack(fill="both", expand=True, padx=16, pady=12)

        col_esq = tk.Frame(cols, bg=COR_BRANCO, relief="solid", bd=1)
        col_dir = tk.Frame(cols, bg=COR_BRANCO, relief="solid", bd=1)
        col_esq.pack(side="left", fill="both", expand=True, padx=(0, 6))
        col_dir.pack(side="left", fill="both", expand=True, padx=(6, 0))

        def titulo_col(parent, texto):
            tk.Label(parent, text=texto, font=FONTE_SECAO,
                     bg=COR_AZUL_MED, fg=COR_BRANCO,
                     pady=4).pack(fill="x")

        def linha(parent, label, valor, destaque=False):
            f = tk.Frame(parent, bg=COR_BRANCO)
            f.pack(fill="x", padx=8, pady=2)
            tk.Label(f, text=label, font=FONTE, bg=COR_BRANCO,
                     fg=COR_TEXTO, anchor="w", width=22).pack(side="left")
            tk.Label(f, text=valor,
                     font=FONTE_SECAO if destaque else FONTE,
                     bg=COR_BRANCO,
                     fg=COR_AZUL if destaque else COR_TEXTO,
                     anchor="e").pack(side="right")

        valor_produto = ent["valor_usd"] * ent["cotacao"]

        titulo_col(col_esq, "Composição do Custo")
        linha(col_esq, "Valor do produto",   f"R$ {valor_produto:,.2f}")
        linha(col_esq, "Frete",              f"R$ {imp['valor_aduaneiro'] - valor_produto:,.2f}")
        linha(col_esq, f"II ({resultado['categoria']['aliquota_ii']*100:.0f}%)",  f"R$ {imp['ii']:,.2f}")
        linha(col_esq, f"IPI ({resultado['categoria']['aliquota_ipi']*100:.0f}%)",f"R$ {imp['ipi']:,.2f}")
        linha(col_esq, "PIS (2,10%)",        f"R$ {imp['pis']:,.2f}")
        linha(col_esq, "COFINS (9,65%)",     f"R$ {imp['cofins']:,.2f}")
        linha(col_esq, f"ICMS ({resultado['aliquota_icms']*100:.0f}%)", f"R$ {imp['icms']:,.2f}")
        linha(col_esq, "Outras despesas",f"R$ {imp['despesas']:,.2f}")
        tk.Frame(col_esq, bg=COR_AZUL_MED, height=1).pack(fill="x", padx=8, pady=4)
        linha(col_esq, "Total de impostos",  f"R$ {imp['total_impostos']:,.2f}")
        linha(col_esq, "Custo unitário",     f"R$ {prec['custo_unitario']:,.2f}", destaque=True)

        titulo_col(col_dir, "Precificação")
        linha(col_dir, "Margem de lucro",    f"{prec['margem_percentual']:.1f}%")
        linha(col_dir, "Preço de venda",     f"R$ {prec['preco_venda']:,.2f}", destaque=True)
        linha(col_dir, "Lucro unitário",     f"R$ {prec['lucro_unitario']:,.2f}")
        tk.Frame(col_dir, bg=COR_AZUL_MED, height=1).pack(fill="x", padx=8, pady=4)
        linha(col_dir, "Quantidade",         f"{prec['quantidade']} un.")
        linha(col_dir, "Receita total",      f"R$ {prec['receita_total']:,.2f}")
        linha(col_dir, "Lucro do lote",      f"R$ {prec['lucro_total_lote']:,.2f}", destaque=True)

        # Rodape fixo com botoes sempre visiveis
        tk.Frame(self, bg=COR_AZUL_MED, height=1).pack(fill="x")
        rodape = tk.Frame(self, bg=COR_CINZA)
        rodape.pack(fill="x", padx=16, pady=10)

        texto_btn = "Já salvo" if self._ja_salvo else "Salvar produto"
        estado_btn = "disabled" if self._ja_salvo else "normal"
        self._btn_salvar = ttk.Button(rodape, text=texto_btn,
                                      command=self._salvar,
                                      state=estado_btn)
        self._btn_salvar.pack(side="left", padx=(0, 8))
        ttk.Button(rodape, text="Ver gráfico de composição",
                   command=self._abrir_grafico).pack(side="left")
        ttk.Button(rodape, text="Fechar",
                   command=self.destroy).pack(side="right")

    def _salvar(self):
        if self._resultado is None:
            return
        try:
            salvo = salvar_produto(self._resultado["entrada"]["nome"], self._resultado)
            self._btn_salvar.configure(state="disabled", text="Salvo")
            messagebox.showinfo("Salvo",
                                f"Produto salvo com ID {salvo['id']}.", parent=self)
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e), parent=self)

    def _abrir_grafico(self):
        from interfaces.janelas.graficos import JanelaGraficos
        JanelaGraficos(self, resultado_inicial=self._resultado)