"""
icms.py
-------
Interface publica para consulta de aliquotas de ICMS.

O controller deve usar apenas este modulo. A fonte de dados atual e JSON,
definida em icms_json.py. Para trocar a fonte, substitua o import
abaixo sem alterar este arquivo nem o controller.
"""

import os
from modulos.icms_json import _carregar

_CAMINHO_PADRAO = os.path.join(
    os.path.dirname(__file__), "..", "dados", "icms.json"
)


def obter_aliquota(uf_origem: str, uf_destino: str,
                   caminho: str = _CAMINHO_PADRAO) -> float:
    """
    Retorna a aliquota de ICMS aplicavel entre dois estados.

    Se origem == destino, retorna a aliquota interna do estado.
    Caso contrario, retorna a aliquota interestadual.
    Se a aliquota interestadual for None, usa a aliquota interna
    do estado de destino.

    Parametros:
        uf_origem : UF de origem (ex: "SP")
        uf_destino: UF de destino (ex: "MG")
        caminho   : caminho para o arquivo icms.json (opcional)

    Retorna:
        float: aliquota de ICMS (ex: 0.18)

    Lanca:
        ValueError: se alguma UF nao for encontrada nas tabelas
    """
    origem  = uf_origem.strip().upper()
    destino = uf_destino.strip().upper()
    dados   = _carregar(caminho)

    interno       = dados["interno"]
    interestadual = dados["interestadual"]

    if origem == destino:
        if origem not in interno:
            raise ValueError(f"UF '{origem}' nao encontrada na tabela de ICMS interno.")
        return interno[origem]

    if origem not in interestadual or destino not in interestadual[origem]:
        raise ValueError(
            f"Combinacao '{origem}' -> '{destino}' nao encontrada "
            f"na tabela de ICMS interestadual."
        )

    aliquota = interestadual[origem][destino]

    # None indica que a operacao usa a aliquota interna do estado de destino
    if aliquota is None:
        if destino not in interno:
            raise ValueError(
                f"UF '{destino}' nao encontrada na tabela de ICMS interno."
            )
        return interno[destino]

    return aliquota


def listar_ufs(caminho: str = _CAMINHO_PADRAO) -> list:
    """
    Retorna lista ordenada de UFs disponiveis.

    Parametros:
        caminho : caminho para o arquivo icms.json (opcional)

    Retorna:
        list de strings: ["AC", "AL", "AM", ...]
    """
    dados = _carregar(caminho)
    return sorted(dados["interno"].keys())