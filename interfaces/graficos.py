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
# Graficos
# ---------------------------------------------------------------------------

def composicao_custo(resultado: dict, caminho: str = None) -> None:
    """
    Gera grafico de pizza com a composicao do custo do produto.

    Exibe o valor aduaneiro e cada imposto como fatias individuais,
    permitindo visualizar o peso de cada tributo no custo final.

    Parametros:
        resultado : dicionario retornado por controller.calcular_produto()
        caminho   : se informado, salva o grafico neste caminho (.png, .pdf)
                    se None, exibe na tela
    """
    imp  = resultado["impostos"]
    nome = resultado["entrada"]["nome"]

    labels = [
        "Valor Aduaneiro",
        f"II ({resultado['categoria']['aliquota_ii']*100:.0f}%)",
        f"IPI ({resultado['categoria']['aliquota_ipi']*100:.0f}%)",
        "PIS (2,10%)",
        "COFINS (9,65%)",
        f"ICMS ({resultado['aliquota_icms']*100:.0f}%)",
        "Despesas Aduaneiras",
    ]
    valores = [
        imp["valor_aduaneiro"],
        imp["ii"],
        imp["ipi"],
        imp["pis"],
        imp["cofins"],
        imp["icms"],
        imp["despesas"],
    ]

    # Remove fatias com valor zero para nao poluir o grafico
    pares = [(l, v) for l, v in zip(labels, valores) if v > 0]
    labels, valores = zip(*pares)

    cores = ["#4C72B0", "#DD8452", "#55A868", "#C44E52",
             "#8172B2", "#937860", "#A8C7E8"][:len(valores)]

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

    custo_total = imp["custo_total"]
    ax.set_title(
        f"Composicao do Custo — {nome}\n"
        f"Custo total: R$ {custo_total:,.2f}",
        fontsize=12,
        pad=16,
    )

    _salvar_ou_exibir(caminho)


def comparativo_produtos(resultados: list, caminho: str = None) -> None:
    """
    Gera grafico de barras empilhadas comparando multiplos produtos.

    Cada barra representa um produto, com segmentos para valor aduaneiro,
    total de impostos e margem de lucro.

    Parametros:
        resultados : lista de dicionarios retornados por calcular_produto()
                     cada dict deve conter a chave 'entrada'['nome']
        caminho    : caminho para salvar o grafico (opcional)

    Lanca:
        ValueError: se a lista de resultados estiver vazia
    """
    if not resultados:
        raise ValueError("A lista de resultados nao pode estar vazia.")

    nomes        = [r["entrada"]["nome"][:20]         for r in resultados]
    aduaneiros   = [r["impostos"]["valor_aduaneiro"]  for r in resultados]
    impostos     = [r["impostos"]["total_impostos"]   for r in resultados]
    despesas     = [r["impostos"]["despesas"]         for r in resultados]
    margens      = [r["precificacao"]["lucro_unitario"] for r in resultados]

    x = range(len(nomes))
    largura = 0.5

    fig, ax = plt.subplots(figsize=(max(6, len(nomes) * 1.5), 6))

    b1 = ax.bar(x, aduaneiros, largura, label="Valor Aduaneiro", color="#4C72B0")
    b2 = ax.bar(x, impostos,   largura, bottom=aduaneiros,
                label="Total Impostos", color="#DD8452")
    b3 = ax.bar(x, despesas,   largura,
                bottom=[a + i for a, i in zip(aduaneiros, impostos)],
                label="Despesas", color="#C44E52")
    b4 = ax.bar(x, margens,    largura,
                bottom=[a + i + d for a, i, d in zip(aduaneiros, impostos, despesas)],
                label="Margem de Lucro", color="#55A868")

    ax.set_xticks(list(x))
    ax.set_xticklabels(nomes, rotation=20, ha="right", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_formatar_reais))
    ax.set_ylabel("Valor (R$)")
    ax.set_title("Comparativo de Produtos — Composicao do Preco de Venda", fontsize=12)
    ax.legend(loc="upper left", fontsize=9)

    _salvar_ou_exibir(caminho)


def ponto_equilibrio(resultado: dict, custo_fixo: float,
                     caminho: str = None) -> None:
    """
    Gera grafico de ponto de equilibrio para o produto.

    Plota as curvas de receita total e custo total em funcao da
    quantidade vendida, destacando o ponto de equilibrio.

    Parametros:
        resultado  : dicionario retornado por calcular_produto()
        custo_fixo : custo fixo total do periodo em reais
        caminho    : caminho para salvar o grafico (opcional)

    Lanca:
        ValueError: se o preco de venda for menor ou igual ao custo unitario
    """
    prec         = resultado["precificacao"]
    nome         = resultado["entrada"]["nome"]
    custo_unit   = prec["custo_unitario"]
    preco_venda  = prec["preco_venda"]

    margem_contrib = preco_venda - custo_unit
    if margem_contrib <= 0:
        raise ValueError(
            "Preco de venda menor ou igual ao custo unitario. "
            "Ponto de equilibrio inexistente."
        )

    pe = custo_fixo / margem_contrib
    qtd_max = int(pe * 2) + 1

    quantidades  = list(range(0, qtd_max + 1))
    custo_total  = [custo_fixo + custo_unit * q for q in quantidades]
    receita      = [preco_venda * q             for q in quantidades]

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(quantidades, receita,     label="Receita Total",  color="#55A868", linewidth=2)
    ax.plot(quantidades, custo_total, label="Custo Total",    color="#C44E52", linewidth=2)
    ax.axhline(custo_fixo, linestyle="--", color="#888", linewidth=1, label="Custo Fixo")
    ax.axvline(pe, linestyle=":",    color="#4C72B0", linewidth=1.5,
               label=f"PE = {pe:.1f} un.")

    ax.annotate(
        f"PE\n{pe:.1f} un.",
        xy=(pe, custo_fixo + margem_contrib * pe),
        xytext=(pe * 1.08, custo_fixo * 1.2),
        arrowprops=dict(arrowstyle="->", color="#4C72B0"),
        fontsize=9, color="#4C72B0",
    )

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_formatar_reais))
    ax.set_xlabel("Quantidade (unidades)")
    ax.set_ylabel("Valor (R$)")
    ax.set_title(f"Ponto de Equilibrio — {nome}", fontsize=12)
    ax.legend(fontsize=9)

    _salvar_ou_exibir(caminho)


def comparativo_estados(resultado_base: dict, estados: list,
                        calcular_fn, caminho: str = None) -> None:
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

    fig, ax = plt.subplots(figsize=(max(6, len(estados) * 0.9), 5))

    cores = ["#C44E52" if uf == entrada_base["uf_destino"] else "#4C72B0"
             for uf in estados]
    bars = ax.bar(estados, precos, color=cores)

    for bar, icms in zip(bars, icms_vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(precos) * 0.01,
            f"ICMS\nR${icms:,.0f}",
            ha="center", va="bottom", fontsize=8,
        )

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_formatar_reais))
    ax.set_ylabel("Preco de Venda (R$)")
    ax.set_title(
        f"Preco de Venda por Estado de Destino — {entrada_base['nome']}\n"
        f"(destino atual destacado em vermelho)",
        fontsize=11,
    )

    _salvar_ou_exibir(caminho)