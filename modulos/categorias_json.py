"""
categorias_json.py
------------------
Camada de acesso a dados: leitura da tabela de categorias em JSON.

Nao deve ser chamado diretamente pelo controller.
Use as funcoes publicas em categorias.py.
"""

import os
from modulos.armazenamento import JsonArmazenamento

_CAMINHO_PADRAO = os.path.join(
    os.path.dirname(__file__), "..", "dados", "categorias.json"
)


def _carregar(caminho: str) -> dict:
    """
    Le o arquivo JSON de categorias e retorna um dicionario indexado
    pela chave 'categoria'.

    Parametros:
        caminho : caminho para o arquivo categorias.json

    Retorna:
        dict no formato:
            {
                "eletronicos": {
                    "descricao"   : "Smartphones e tablets",
                    "aliquota_ii" : 0.16,
                    "aliquota_ipi": 0.15,
                },
                ...
            }

    Lanca:
        FileNotFoundError: se o arquivo nao for encontrado
        ValueError: se o arquivo estiver corrompido
    """
    armazenamento = JsonArmazenamento(caminho, valor_padrao={})
    dados = armazenamento.carregar()

    if not dados:
        raise FileNotFoundError(
            f"Arquivo de categorias vazio ou nao encontrado: {caminho}"
        )
    return dados