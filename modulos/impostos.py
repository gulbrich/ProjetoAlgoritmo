"""
impostos.py
-----------
Calculo dos impostos incidentes sobre produtos importados no Brasil.

Ordem de calculo (cascata):
    1. Valor Aduaneiro (VA)
    2. Imposto de Importacao (II)       - base: VA
    3. IPI                              - base: VA + II
    4. PIS-Importacao                   - base: VA
    5. COFINS-Importacao                - base: VA
    6. ICMS (calculo "por dentro")      - base: VA + II + IPI + PIS + COFINS + despesas

Referencias:
    - II e IPI : Receita Federal / TIPI
    - PIS/COFINS: Lei 10.865/2004 (aliquotas 2,10% e 9,65%)
    - ICMS      : base "por dentro" conforme legislacao estadual
"""

# Aliquotas federais fixas de PIS e COFINS na importacao (Lei 10.865/2004)
ALIQUOTA_PIS    = 0.0210
ALIQUOTA_COFINS = 0.0965


def _validar_entradas(valor_usd: float, cotacao: float, frete: float,
                      aliquota_ii: float, aliquota_ipi: float,
                      aliquota_icms: float, despesas: float) -> None:
    """
    Valida os parametros de entrada antes do calculo.

    Lanca:
        TypeError : se algum parametro nao for numerico
        ValueError: se algum parametro estiver fora do intervalo esperado
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
            raise TypeError(f"'{nome}' deve ser numerico, recebido: {type(valor).__name__}.")

    for nome, valor in campos_positivos.items():
        if valor <= 0:
            raise ValueError(f"'{nome}' deve ser maior que zero, recebido: {valor}.")

    for nome, valor in campos_nao_negativos.items():
        if valor < 0:
            raise ValueError(f"'{nome}' nao pode ser negativo, recebido: {valor}.")

    for nome, valor in aliquotas.items():
        if not (0 <= valor < 1):
            raise ValueError(
                f"'{nome}' deve estar entre 0 e 1 (ex: 0.18 para 18%), recebido: {valor}."
            )


def calcular_valor_aduaneiro(valor_usd: float, cotacao: float, frete: float) -> float:
    """
    Calcula o Valor Aduaneiro (VA), base de todos os impostos.

    Parametros:
        valor_usd : valor do produto em dolares
        cotacao   : cotacao do dolar em reais (R$/USD)
        frete     : frete internacional em reais

    Retorna:
        float: valor aduaneiro em reais
    """
    return (valor_usd * cotacao) + frete


def calcular_ii(valor_aduaneiro: float, aliquota: float) -> float:
    """
    Calcula o Imposto de Importacao (II).

    Base de calculo: Valor Aduaneiro.

    Parametros:
        valor_aduaneiro : base de calculo em reais
        aliquota        : aliquota do II (ex: 0.16 para 16%)

    Retorna:
        float: valor do II em reais
    """
    return valor_aduaneiro * aliquota


def calcular_ipi(valor_aduaneiro: float, ii: float, aliquota: float) -> float:
    """
    Calcula o Imposto sobre Produtos Industrializados (IPI).

    Base de calculo: Valor Aduaneiro + II.

    Parametros:
        valor_aduaneiro : base inicial em reais
        ii              : valor do II ja calculado
        aliquota        : aliquota do IPI (ex: 0.15 para 15%)

    Retorna:
        float: valor do IPI em reais
    """
    return (valor_aduaneiro + ii) * aliquota


def calcular_pis(valor_aduaneiro: float) -> float:
    """
    Calcula o PIS-Importacao.

    Base de calculo: Valor Aduaneiro (Lei 10.865/2004).
    Aliquota fixa: 2,10%.

    Parametros:
        valor_aduaneiro : base de calculo em reais

    Retorna:
        float: valor do PIS em reais
    """
    return valor_aduaneiro * ALIQUOTA_PIS


def calcular_cofins(valor_aduaneiro: float) -> float:
    """
    Calcula a COFINS-Importacao.

    Base de calculo: Valor Aduaneiro (Lei 10.865/2004).
    Aliquota fixa: 9,65%.

    Parametros:
        valor_aduaneiro : base de calculo em reais

    Retorna:
        float: valor da COFINS em reais
    """
    return valor_aduaneiro * ALIQUOTA_COFINS


def calcular_icms(valor_aduaneiro: float, ii: float, ipi: float,
                  pis: float, cofins: float, despesas: float,
                  aliquota: float) -> float:
    """
    Calcula o ICMS na importacao pelo metodo "por dentro".

    O ICMS integra sua propria base de calculo, exigindo formula fechada:
        ICMS = base_parcial * aliquota / (1 - aliquota)
    onde:
        base_parcial = VA + II + IPI + PIS + COFINS + despesas_aduaneiras

    Nota: despesas aduaneiras entram na base do ICMS mas nao sao imposto.
    Elas sao somadas ao custo_total separadamente em calcular_todos().

    Parametros:
        valor_aduaneiro : VA em reais
        ii              : valor do II
        ipi             : valor do IPI
        pis             : valor do PIS
        cofins          : valor da COFINS
        despesas        : despesas aduaneiras (SISCOMEX, despachante, etc.)
        aliquota        : aliquota do ICMS do estado (ex: 0.18 para 18%)

    Retorna:
        float: valor do ICMS em reais
    """
    base_parcial = valor_aduaneiro + ii + ipi + pis + cofins + despesas
    return base_parcial * aliquota / (1 - aliquota)


def calcular_todos(valor_usd: float, cotacao: float, frete: float,
                   aliquota_ii: float, aliquota_ipi: float,
                   aliquota_icms: float, despesas: float) -> dict:
    """
    Executa o calculo completo de todos os impostos em cascata.

    Os valores intermediarios circulam sem arredondamento para evitar
    acumulo de erro. O arredondamento ocorre apenas no retorno final.
    Os campos 'total_impostos' e 'custo_total' sao calculados a partir
    dos valores nao arredondados, garantindo consistencia interna.

    Nota sobre despesas: entram na base do ICMS e sao somadas ao
    custo_total, mas nao compoe o total_impostos (nao sao tributos).

    Parametros:
        valor_usd    : valor do produto em dolares
        cotacao      : cotacao do dolar em reais
        frete        : frete internacional em reais
        aliquota_ii  : aliquota do Imposto de Importacao (0 a 0.99)
        aliquota_ipi : aliquota do IPI (0 a 0.99)
        aliquota_icms: aliquota do ICMS do estado de destino (0 a 0.99)
        despesas     : despesas aduaneiras em reais (SISCOMEX, despachante, etc.)

    Retorna:
        dict com as chaves:
            valor_aduaneiro, ii, ipi, pis, cofins, icms,
            despesas, total_impostos, custo_total

    Lanca:
        TypeError : se algum parametro nao for numerico
        ValueError: se algum parametro estiver fora do intervalo esperado
    """
    _validar_entradas(valor_usd, cotacao, frete, aliquota_ii, aliquota_ipi, aliquota_icms, despesas)

    va     = calcular_valor_aduaneiro(valor_usd, cotacao, frete)
    ii     = calcular_ii(va, aliquota_ii)
    ipi    = calcular_ipi(va, ii, aliquota_ipi)
    pis    = calcular_pis(va)
    cofins = calcular_cofins(va)
    icms   = calcular_icms(va, ii, ipi, pis, cofins, despesas, aliquota_icms)

    # despesas nao sao imposto — somam ao custo mas nao ao total_impostos
    total_impostos = ii + ipi + pis + cofins + icms
    custo_total    = va + total_impostos + despesas

    return {
        "valor_aduaneiro" : round(va,             2),
        "ii"              : round(ii,             2),
        "ipi"             : round(ipi,            2),
        "pis"             : round(pis,            2),
        "cofins"          : round(cofins,         2),
        "icms"            : round(icms,           2),
        "despesas"        : round(despesas,       2),
        "total_impostos"  : round(total_impostos, 2),
        "custo_total"     : round(custo_total,    2),
    }