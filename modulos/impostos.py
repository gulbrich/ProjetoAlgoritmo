"""
impostos.py
-----------
Cálculo dos impostos incidentes sobre produtos importados no Brasil.

Ordem de cálculo (cascata):
    1. Valor Aduaneiro (VA)
    2. Imposto de Importação (II)       - base: VA
    3. IPI                              - base: VA + II
    4. PIS-Importação                   - base: VA
    5. COFINS-Importação                - base: VA
    6. ICMS (cálculo "por dentro")      - base: VA + II + IPI + PIS + COFINS + despesas

Referências:
    - II e IPI : Receita Federal / TIPI
    - PIS/COFINS: Lei 10.865/2004 (alíquotas 2,10% e 9,65%)
    - ICMS      : base "por dentro" conforme legislação estadual
"""

# Alíquotas federais fixas de PIS e COFINS na importação (Lei 10.865/2004)
ALIQUOTA_PIS    = 0.0210
ALIQUOTA_COFINS = 0.0965


def _validar_entradas(valor_usd: float, cotacao: float, frete: float,
                      aliquota_ii: float, aliquota_ipi: float,
                      aliquota_icms: float, despesas: float) -> None:
    """
    Valida os parâmetros de entrada antes do cálculo.

    Lança:
        TypeError : se algum parâmetro não for numérico
        ValueError: se algum parâmetro estiver fora do intervalo esperado
    """
    campos_positivos = {
        "valor_usd": valor_usd,
        "cotacao"  : cotacao,
    }
    campos_nao_negativos = {
        "frete"   : frete,
        "despesas": despesas,
    }
    aliquotas = {
        "aliquota_ii"  : aliquota_ii,
        "aliquota_ipi" : aliquota_ipi,
        "aliquota_icms": aliquota_icms,
    }

    for nome, valor in {**campos_positivos, **campos_nao_negativos, **aliquotas}.items():
        if not isinstance(valor, (int, float)):
            raise TypeError(f"'{nome}' deve ser numérico, recebido: {type(valor).__name__}.")

    for nome, valor in campos_positivos.items():
        if valor <= 0:
            raise ValueError(f"'{nome}' deve ser maior que zero, recebido: {valor}.")

    for nome, valor in campos_nao_negativos.items():
        if valor < 0:
            raise ValueError(f"'{nome}' não pode ser negativo, recebido: {valor}.")

    for nome, valor in aliquotas.items():
        if not (0 <= valor < 1):
            raise ValueError(
                f"'{nome}' deve estar entre 0 e 1 (ex: 0.18 para 18%), recebido: {valor}."
            )


def calcular_valor_aduaneiro(valor_usd: float, cotacao: float, frete: float) -> float:
    """
    Calcula o Valor Aduaneiro (VA), base de todos os impostos.

    Parâmetros:
        valor_usd : valor do produto em dólares
        cotacao   : cotação do dólar em reais (R$/USD)
        frete     : frete internacional em reais

    Retorna:
        float: valor aduaneiro em reais
    """
    return (valor_usd * cotacao) + frete


def calcular_ii(valor_aduaneiro: float, aliquota: float) -> float:
    """
    Calcula o Imposto de Importação (II).

    Base de cálculo: Valor Aduaneiro.

    Parâmetros:
        valor_aduaneiro : base de cálculo em reais
        aliquota        : alíquota do II (ex: 0.16 para 16%)

    Retorna:
        float: valor do II em reais
    """
    return valor_aduaneiro * aliquota


def calcular_ipi(valor_aduaneiro: float, ii: float, aliquota: float) -> float:
    """
    Calcula o Imposto sobre Produtos Industrializados (IPI).

    Base de cálculo: Valor Aduaneiro + II.

    Parâmetros:
        valor_aduaneiro : base inicial em reais
        ii              : valor do II já calculado
        aliquota        : alíquota do IPI (ex: 0.15 para 15%)

    Retorna:
        float: valor do IPI em reais
    """
    return (valor_aduaneiro + ii) * aliquota


def calcular_pis(valor_aduaneiro: float) -> float:
    """
    Calcula o PIS-Importação.

    Base de cálculo: Valor Aduaneiro (Lei 10.865/2004).
    Alíquota fixa: 2,10%.

    Parâmetros:
        valor_aduaneiro : base de cálculo em reais

    Retorna:
        float: valor do PIS em reais
    """
    return valor_aduaneiro * ALIQUOTA_PIS


def calcular_cofins(valor_aduaneiro: float) -> float:
    """
    Calcula a COFINS-Importação.

    Base de cálculo: Valor Aduaneiro (Lei 10.865/2004).
    Alíquota fixa: 9,65%.

    Parâmetros:
        valor_aduaneiro : base de cálculo em reais

    Retorna:
        float: valor da COFINS em reais
    """
    return valor_aduaneiro * ALIQUOTA_COFINS


def calcular_icms(valor_aduaneiro: float, ii: float, ipi: float,
                  pis: float, cofins: float, despesas: float,
                  aliquota: float) -> float:
    """
    Calcula o ICMS na importação pelo método "por dentro".

    O ICMS integra sua própria base de cálculo, exigindo fórmula fechada:
        ICMS = base_parcial * aliquota / (1 - aliquota)
    onde:
        base_parcial = VA + II + IPI + PIS + COFINS + despesas_aduaneiras

    Parâmetros:
        valor_aduaneiro : VA em reais
        ii              : valor do II
        ipi             : valor do IPI
        pis             : valor do PIS
        cofins          : valor da COFINS
        despesas        : despesas aduaneiras (SISCOMEX, despachante, etc.)
        aliquota        : alíquota do ICMS do estado (ex: 0.18 para 18%)

    Retorna:
        float: valor do ICMS em reais
    """
    base_parcial = valor_aduaneiro + ii + ipi + pis + cofins + despesas
    return base_parcial * aliquota / (1 - aliquota)


def calcular_todos(valor_usd: float, cotacao: float, frete: float,
                   aliquota_ii: float, aliquota_ipi: float,
                   aliquota_icms: float, despesas: float,
                   quantidade: int = 1) -> dict:
    """
    Executa o cálculo completo de todos os impostos em cascata.

    Frete e despesas são valores totais do lote e são rateados pela
    quantidade antes do cálculo, garantindo que o custo unitário
    reflita corretamente a participação de cada unidade nesses custos.

    Os valores intermediários circulam sem arredondamento para evitar
    acúmulo de erro. O arredondamento ocorre apenas no retorno final.
    Os campos 'total_impostos' e 'custo_total' são valores unitários.

    Nota sobre despesas: entram na base do ICMS e são somadas ao
    custo_total, mas não compõem o total_impostos (não são tributos).

    Parâmetros:
        valor_usd    : valor do produto em dólares (por unidade)
        cotacao      : cotação do dólar em reais
        frete        : frete internacional total do lote em reais
        aliquota_ii  : alíquota do Imposto de Importação (0 a 0.99)
        aliquota_ipi : alíquota do IPI (0 a 0.99)
        aliquota_icms: alíquota do ICMS do estado de destino (0 a 0.99)
        despesas     : despesas aduaneiras totais do lote em reais
        quantidade   : número de unidades do lote (default: 1)

    Retorna:
        dict com as chaves (todos valores unitários):
            valor_aduaneiro, ii, ipi, pis, cofins, icms,
            frete_unitario, despesas_unitario,
            total_impostos, custo_total,
            frete_lote, despesas_lote

    Lança:
        TypeError : se algum parâmetro não for numérico
        ValueError: se algum parâmetro estiver fora do intervalo esperado
    """
    if not isinstance(quantidade, int) or quantidade < 1:
        raise ValueError(f"'quantidade' deve ser um inteiro maior que zero, recebido: {quantidade}.")

    _validar_entradas(valor_usd, cotacao, frete, aliquota_ii, aliquota_ipi, aliquota_icms, despesas)

    # Ratear frete e despesas do lote por unidade
    frete_unit    = frete    / quantidade
    despesas_unit = despesas / quantidade

    va     = calcular_valor_aduaneiro(valor_usd, cotacao, frete_unit)
    ii     = calcular_ii(va, aliquota_ii)
    ipi    = calcular_ipi(va, ii, aliquota_ipi)
    pis    = calcular_pis(va)
    cofins = calcular_cofins(va)
    icms   = calcular_icms(va, ii, ipi, pis, cofins, despesas_unit, aliquota_icms)

    # Despesas não são imposto — somam ao custo mas não ao total_impostos
    total_impostos = ii + ipi + pis + cofins + icms
    custo_total    = va + total_impostos + despesas_unit

    return {
        "valor_aduaneiro"  : round(va,             2),
        "ii"               : round(ii,             2),
        "ipi"              : round(ipi,            2),
        "pis"              : round(pis,            2),
        "cofins"           : round(cofins,         2),
        "icms"             : round(icms,           2),
        "frete_unitario"   : round(frete_unit,     2),
        "despesas_unitario": round(despesas_unit,  2),
        "despesas"         : round(despesas_unit,  2),  # compatibilidade
        "total_impostos"   : round(total_impostos, 2),
        "custo_total"      : round(custo_total,    2),
        "frete_lote"       : round(frete,          2),
        "despesas_lote"    : round(despesas,       2),
    }