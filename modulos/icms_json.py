"""
icms_json.py
------------
Camada de acesso a dados: leitura das tabelas de ICMS em JSON.

Nao deve ser chamado diretamente pelo controller.
Use as funcoes publicas em icms.py.

Estrutura esperada do arquivo icms.json:
{
  "interno": {
    "SP": 0.18,
    "MG": 0.18,
    ...
  },
  "interestadual": {
    "SP": { "MG": 0.12, "BA": 0.07, ... },
    ...
  }
}
"""

import os
from modulos.armazenamento import JsonArmazenamento

_CAMINHO_PADRAO = os.path.join(
    os.path.dirname(__file__), "..", "dados", "icms.json"
)


def _carregar(caminho: str) -> dict:
    """
    Le o arquivo JSON de ICMS e retorna o dicionario completo.

    Parametros:
        caminho : caminho para o arquivo icms.json

    Retorna:
        dict com chaves 'interno' e 'interestadual'

    Lanca:
        FileNotFoundError: se o arquivo nao for encontrado
        ValueError: se o arquivo estiver corrompido ou mal estruturado
    """
    armazenamento = JsonArmazenamento(caminho, valor_padrao={})
    dados = armazenamento.carregar()

    if not dados:
        raise FileNotFoundError(
            f"Arquivo de ICMS vazio ou nao encontrado: {caminho}"
        )
    if "interno" not in dados or "interestadual" not in dados:
        raise ValueError(
            f"Arquivo de ICMS mal estruturado. "
            f"Esperado: chaves 'interno' e 'interestadual'."
        )
    return dados