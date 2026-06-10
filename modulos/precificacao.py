"""
precificacao.py
---------------
Calculo do preco de venda e indicadores de rentabilidade
a partir do custo total de um produto importado.

Formula de markup:
    preco_venda = custo_total / (1 - margem_desejada)

Essa formula garante que a margem de lucro seja calculada
sobre o preco de venda, nao sobre o custo (markup "por dentro"),
que e a pratica mais comum no comercio.
"""


def _validar_entradas(custo_total: float, margem: float,
                      quantidade: int) -> None:
    """
    Valida os parametros antes do calculo.

    Lanca:
        TypeError : se algum parametro nao for do tipo esperado
        ValueError: se algum parametro estiver fora do intervalo valido
    """
    if not isinstance(custo_total, (int, float)):
        raise TypeError(f"'custo_total' deve ser numerico, recebido: {type(custo_total).__name__}.")
    if not isinstance(margem, (int, float)):
        raise TypeError(f"'margem' deve ser numerica, recebida: {type(margem).__name__}.")
    if not isinstance(quantidade, int):
        raise TypeError(f"'quantidade' deve ser inteiro, recebida: {type(quantidade).__name__}.")

    if custo_total <= 0:
        raise ValueError(f"'custo_total' deve ser maior que zero, recebido: {custo_total}.")
    if not (0 < margem < 1):
        raise ValueError(
            f"'margem' deve estar entre 0 e 1 (ex: 0.30 para 30%), recebida: {margem}."
        )
    if quantidade <= 0:
        raise ValueError(f"'quantidade' deve ser maior que zero, recebida: {quantidade}.")


def calcular_preco_venda(custo_total: float, margem: float) -> float:
    """
    Calcula o preco de venda unitario usando markup por dentro.

    Formula: preco_venda = custo_total / (1 - margem)

    Parametros:
        custo_total : custo total unitario em reais
        margem      : margem de lucro desejada (ex: 0.30 para 30%)

    Retorna:
        float: preco de venda unitario em reais
    """
    return custo_total / (1 - margem)


def calcular_lucro_unitario(preco_venda: float, custo_total: float) -> float:
    """
    Calcula o lucro bruto por unidade vendida.

    Parametros:
        preco_venda : preco de venda unitario em reais
        custo_total : custo total unitario em reais

    Retorna:
        float: lucro bruto unitario em reais
    """
    return preco_venda - custo_total


def calcular_ponto_equilibrio(custo_fixo: float, custo_total_unitario: float,
                               preco_venda: float) -> float:
    """
    Calcula o ponto de equilibrio em unidades.

    O ponto de equilibrio e a quantidade minima a ser vendida para
    que a receita cubra todos os custos (fixos e variaveis).

    Formula: PE = custo_fixo / (preco_venda - custo_total_unitario)

    Parametros:
        custo_fixo           : custos fixos totais do periodo em reais
        custo_total_unitario : custo variavel por unidade em reais
        preco_venda          : preco de venda unitario em reais

    Retorna:
        float: quantidade minima de unidades para atingir o equilibrio

    Lanca:
        ValueError: se o preco de venda for menor ou igual ao custo unitario
    """
    margem_contribuicao = preco_venda - custo_total_unitario
    if margem_contribuicao <= 0:
        raise ValueError(
            "O preco de venda deve ser maior que o custo unitario para "
            "que exista ponto de equilibrio."
        )
    return custo_fixo / margem_contribuicao


def calcular_resumo(custo_total: float, margem: float,
                    quantidade: int) -> dict:
    """
    Calcula o resumo completo de precificacao para um lote de produtos.

    Parametros:
        custo_total : custo total por unidade em reais
        margem      : margem de lucro desejada (ex: 0.30 para 30%)
        quantidade  : quantidade de unidades do lote

    Retorna:
        dict com as chaves:
            custo_unitario       : custo por unidade
            preco_venda          : preco de venda por unidade
            lucro_unitario       : lucro bruto por unidade
            margem_percentual    : margem em percentual (ex: 30.0)
            receita_total        : receita do lote (preco x quantidade)
            custo_total_lote     : custo do lote (custo x quantidade)
            lucro_total_lote     : lucro bruto do lote
            quantidade           : quantidade de unidades

    Lanca:
        TypeError : se algum parametro nao for do tipo esperado
        ValueError: se algum parametro estiver fora do intervalo valido
    """
    _validar_entradas(custo_total, margem, quantidade)

    preco_venda     = calcular_preco_venda(custo_total, margem)
    lucro_unitario  = calcular_lucro_unitario(preco_venda, custo_total)
    receita_total   = preco_venda * quantidade
    custo_lote      = custo_total * quantidade
    lucro_lote      = lucro_unitario * quantidade

    return {
        "custo_unitario"    : round(custo_total,    2),
        "preco_venda"       : round(preco_venda,    2),
        "lucro_unitario"    : round(lucro_unitario, 2),
        "margem_percentual" : round(margem * 100,   2),
        "receita_total"     : round(receita_total,  2),
        "custo_total_lote"  : round(custo_lote,     2),
        "lucro_total_lote"  : round(lucro_lote,     2),
        "quantidade"        : quantidade,
    }