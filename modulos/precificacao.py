"""
precificacao.py
---------------
Cálculo do preço de venda e indicadores de rentabilidade
a partir do custo total de um produto importado.

Fórmula de markup:
    preco_venda = custo_total / (1 - margem_desejada)

Essa fórmula garante que a margem de lucro seja calculada
sobre o preço de venda, não sobre o custo (markup "por dentro"),
que é a prática mais comum no comércio.
"""


def _validar_entradas(custo_total: float, margem: float,
                      quantidade: int) -> None:
    """
    Valida os parâmetros antes do cálculo.

    Lança:
        TypeError : se algum parâmetro não for do tipo esperado
        ValueError: se algum parâmetro estiver fora do intervalo válido
    """
    if not isinstance(custo_total, (int, float)):
        raise TypeError(f"'custo_total' deve ser numérico, recebido: {type(custo_total).__name__}.")
    if not isinstance(margem, (int, float)):
        raise TypeError(f"'margem' deve ser numérica, recebida: {type(margem).__name__}.")
    if not isinstance(quantidade, int):
        raise TypeError(f"'quantidade' deve ser inteiro, recebida: {type(quantidade).__name__}.")

    if custo_total <= 0:
        raise ValueError(f"'custo_total' deve ser maior que zero, recebido: {custo_total}.")
    if margem <= 0:
        raise ValueError(
            f"'margem' deve ser maior que zero, recebida: {margem}."
        )
    if quantidade <= 0:
        raise ValueError(f"'quantidade' deve ser maior que zero, recebida: {quantidade}.")


def calcular_preco_venda(custo_total: float, margem: float) -> float:
    """
    Calcula o preço de venda unitário.

    Para margens até 99% usa markup por dentro (margem sobre o preço de venda):
        preco_venda = custo_total / (1 - margem)

    Para margens de 100% ou mais usa markup por fora (margem sobre o custo):
        preco_venda = custo_total * (1 + margem)

    Parâmetros:
        custo_total : custo total unitário em reais
        margem      : margem de lucro desejada (ex: 0.30 para 30%, 1.50 para 150%)

    Retorna:
        float: preço de venda unitário em reais
    """
    if margem < 1:
        return custo_total / (1 - margem)
    else:
        return custo_total * (1 + margem)


def calcular_lucro_unitario(preco_venda: float, custo_total: float) -> float:
    """
    Calcula o lucro bruto por unidade vendida.

    Parâmetros:
        preco_venda : preço de venda unitário em reais
        custo_total : custo total unitário em reais

    Retorna:
        float: lucro bruto unitário em reais
    """
    return preco_venda - custo_total


def calcular_resumo(custo_total: float, margem: float,
                    quantidade: int) -> dict:
    """
    Calcula o resumo completo de precificação para um lote de produtos.

    Parâmetros:
        custo_total : custo total por unidade em reais
        margem      : margem de lucro desejada (ex: 0.30 para 30%)
        quantidade  : quantidade de unidades do lote

    Retorna:
        dict com as chaves:
            custo_unitario       : custo por unidade
            preco_venda          : preço de venda por unidade
            lucro_unitario       : lucro bruto por unidade
            margem_percentual    : margem em percentual (ex: 30.0)
            receita_total        : receita do lote (preço x quantidade)
            custo_total_lote     : custo do lote (custo x quantidade)
            lucro_total_lote     : lucro bruto do lote
            quantidade           : quantidade de unidades

    Lança:
        TypeError : se algum parâmetro não for do tipo esperado
        ValueError: se algum parâmetro estiver fora do intervalo válido
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