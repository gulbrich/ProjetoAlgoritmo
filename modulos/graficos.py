"""
graficos.py
-----------
Geracao de graficos para visualizacao dos resultados de precificacao.

Todas as funcoes recebem dicionarios retornados pelo controller
e nao fazem input() ou print(). A exibicao e feita via matplotlib.

Graficos disponiveis:
    - composicao_custo()      : pizza com impostos discriminados
    - comparativo_produtos()  : barras empilhadas por produto
    - ponto_equilibrio()      : receita x custo total com PE destacado
    - comparativo_estados()   : preco de venda por estado de destino
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# ---------------------------------------------------------------------------
# Utilitarios internos
# ---------------------------------------------------------------------------

def _formatar_reais(valor: float, pos=None) -> str:
    """Formata um valor float como moeda brasileira para eixos do matplotlib."""
    return f"R$ {valor:,.0f}".replace(",", ".")


def _salvar_ou_exibir(caminho: str = None) -> None:
    """Salva o grafico em arquivo se caminho fornecido, senao exibe na tela."""
    if caminho:
        plt.savefig(caminho, bbox_inches="tight", dpi=150)
        plt.close()
    else:
        plt.tight_layout()
        plt.show()


# ---------------------------------------------------------------------------
# gráficos
# ---------------------------------------------------------------------------

def composicao_custo(resultado: dict, caminho: str = None,
                     _ax=None) -> None:
    """
    Gera grafico de pizza com a composicao do custo do produto.

    Exibe o valor do produto, frete e cada imposto como fatias individuais,
    permitindo visualizar o peso de cada componente no custo final.

    O valor aduaneiro (VA = produto + frete) e desmembrado para que
    o usuario veja claramente quanto pagou pelo produto em si.

    Parametros:
        resultado : dicionario retornado por controller.calcular_produto()
        caminho   : se informado, salva o grafico neste caminho (.png, .pdf)
                    se None, exibe na tela
        _ax       : eixo matplotlib externo (usado para embutir em GUI tkinter)
    """
    imp     = resultado["impostos"]
    prec    = resultado["precificacao"]
    entrada = resultado["entrada"]
    nome    = entrada["nome"]

    valor_produto = float(entrada["valor_usd"]) * float(entrada["cotacao"])
    frete         = float(entrada["frete"]) / int(entrada.get("quantidade", 1))
    lucro         = prec["lucro_unitario"]

    labels = [
        "Valor do Produto",
        "Frete Internacional",
        f"II ({resultado['categoria']['aliquota_ii']*100:.0f}%)",
        f"IPI ({resultado['categoria']['aliquota_ipi']*100:.0f}%)",
        "PIS (2,10%)",
        "COFINS (9,65%)",
        f"ICMS ({resultado['aliquota_icms']*100:.0f}%)",
        "Outras Despesas",
        "Lucro",
    ]
    valores = [
        valor_produto,
        frete,
        imp["ii"],
        imp["ipi"],
        imp["pis"],
        imp["cofins"],
        imp["icms"],
        imp["despesas"],
        lucro,
    ]

    # Remove fatias com valor zero para não poluir o gráfico
    pares = [(l, v) for l, v in zip(labels, valores) if v > 0]
    labels, valores = zip(*pares)

    # Verde para lucro, cores distintas para os demais
    cores_base = ["#2E75B6", "#A8C7E8", "#DD8452", "#55A868", "#C44E52",
                  "#8172B2", "#937860", "#B5CFE8", "#70AD47"]
    cores = [cores_base[8] if l == "Lucro" else cores_base[i % 8]
             for i, l in enumerate(labels)]

    if _ax is not None:
        ax = _ax
    else:
        fig, ax = plt.subplots(figsize=(8, 6))

    wedges, texts, autotexts = ax.pie(
        valores,
        labels=None,
        autopct="%1.1f%%",
        colors=cores,
        startangle=90,
        pctdistance=0.82,
    )

    for at in autotexts:
        at.set_fontsize(9)

    ax.legend(
        wedges, labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        fontsize=9,
    )

    preco_venda = prec["preco_venda"]
    ax.set_title(
        f"Composição do Preço de Venda — {nome}\n"
        f"Preço de venda: R$ {preco_venda:,.2f}",
        fontsize=12,
        pad=16,
    )

    if _ax is None:
        _salvar_ou_exibir(caminho)


def comparativo_produtos(resultados: list, caminho: str = None,
                         _ax=None) -> None:
    """
    Gera grafico de barras agrupadas comparando multiplos produtos.

    Exibe, para cada produto, o percentual de impostos sobre o custo total
    e a margem de lucro sobre o preco de venda. Usar percentuais em vez de
    valores absolutos permite comparar produtos de escalas de preco muito
    diferentes de forma significativa.

    Parametros:
        resultados : lista de dicionarios retornados por calcular_produto()
        caminho    : caminho para salvar o grafico (opcional)

    Lanca:
        ValueError: se a lista de resultados estiver vazia
    """
    if not resultados:
        raise ValueError("A lista de resultados nao pode estar vazia.")

    nomes = [r["entrada"]["nome"][:20] for r in resultados]

    # % de impostos sobre o custo total
    pct_impostos = [
        r["impostos"]["total_impostos"] / r["impostos"]["custo_total"] * 100
        for r in resultados
    ]
    # % de margem sobre o preco de venda
    pct_margem = [
        r["precificacao"]["lucro_unitario"] / r["precificacao"]["preco_venda"] * 100
        for r in resultados
    ]
    # % de despesas sobre o custo total
    pct_despesas = [
        r["impostos"]["despesas"] / r["impostos"]["custo_total"] * 100
        for r in resultados
    ]

    x       = list(range(len(nomes)))
    largura = 0.25

    if _ax is not None:
        ax = _ax
    else:
        fig, ax = plt.subplots(figsize=(max(6, len(nomes) * 1.8), 6))

    pos_imp  = [xi - largura for xi in x]
    pos_desp = [xi           for xi in x]
    pos_mar  = [xi + largura for xi in x]

    bars_imp  = ax.bar(pos_imp,  pct_impostos, largura, label="Impostos / Custo Total (%)",   color="#DD8452")
    bars_desp = ax.bar(pos_desp, pct_despesas, largura, label="Despesas / Custo Total (%)",   color="#C44E52")
    bars_mar  = ax.bar(pos_mar,  pct_margem,   largura, label="Margem / Preco de Venda (%)",  color="#55A868")

    for bars in [bars_imp, bars_desp, bars_mar]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.4,
                        f"{h:.1f}%", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(nomes, rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("Percentual (%)")
    ax.set_ylim(0, max(max(pct_impostos), max(pct_margem)) * 1.18)
    ax.set_title("Comparativo de Produtos — Carga Tributaria e Margem (%)", fontsize=12)
    ax.legend(loc="upper right", fontsize=9)

    if _ax is None:
        _salvar_ou_exibir(caminho)


def comparativo_estados(resultado_base: dict, estados: list,
                        calcular_fn, caminho: str = None,
                        _ax=None) -> None:
    """
    Gera grafico de barras com o preco de venda por estado de destino.

    Util para comparar o impacto do ICMS interestadual no preco final.

    Parametros:
        resultado_base : resultado de calcular_produto() usado como base
        estados        : lista de UFs a comparar (ex: ["SP","MG","BA","RS"])
        calcular_fn    : funcao controller.calcular_produto, passada como
                         argumento para evitar importacao circular
        caminho        : caminho para salvar o grafico (opcional)

    Lanca:
        ValueError: se a lista de estados estiver vazia
    """
    if not estados:
        raise ValueError("A lista de estados nao pode estar vazia.")

    entrada_base = resultado_base["entrada"].copy()
    precos, icms_vals = [], []

    for uf in estados:
        entrada = {**entrada_base, "uf_destino": uf}
        r = calcular_fn(entrada)
        precos.append(r["precificacao"]["preco_venda"])
        icms_vals.append(r["impostos"]["icms"])

    if _ax is not None:
        ax = _ax
    else:
        fig, ax = plt.subplots(figsize=(max(6, len(estados) * 0.9), 5))

    cores = ["#C44E52" if uf == entrada_base["uf_destino"] else "#4C72B0"
             for uf in estados]
    bars = ax.bar(estados, precos, color=cores)

    preco_base = precos[estados.index(entrada_base["uf_destino"])] if entrada_base["uf_destino"] in estados else precos[0]

    for bar, preco, uf in zip(bars, precos, estados):
        diff = preco - preco_base
        if uf == entrada_base["uf_destino"]:
            rotulo = "base"
        elif diff >= 0:
            rotulo = f"+R${diff:,.0f}"
        else:
            rotulo = f"-R${abs(diff):,.0f}"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(precos) * 0.01,
            rotulo,
            ha="center", va="bottom", fontsize=8,
            color="#C44E52" if diff > 0 else "#55A868" if diff < 0 else "#444444",
        )

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_formatar_reais))
    ax.set_ylabel("Preco de Venda (R$)")
    ax.set_title(
        f"Preco de Venda por Estado de Destino — {entrada_base['nome']}\n"
        f"(valores mostram diferenca em relacao ao estado base)",
        fontsize=11,
    )

    if _ax is None:
        _salvar_ou_exibir(caminho)