"""
repositorio_json.py
-------------------
Camada de acesso a dados: leitura e escrita do cadastro de produtos em JSON.

Nao deve ser chamado diretamente pelo controller.
Use as funcoes publicas em repositorio.py.
"""

import os
from modulos.armazenamento import JsonArmazenamento

_CAMINHO_PADRAO = os.path.join(
    os.path.dirname(__file__), "..", "dados", "produtos.json"
)


def _carregar(caminho: str) -> list:
    """
    Le o arquivo JSON e retorna a lista de produtos cadastrados.

    Retorna lista vazia se o arquivo nao existir (primeiro uso).

    Parametros:
        caminho : caminho para o arquivo produtos.json

    Retorna:
        list de dicionarios representando os produtos

    Lanca:
        ValueError: se o arquivo existir mas estiver corrompido
    """
    armazenamento = JsonArmazenamento(caminho, valor_padrao=[])
    return armazenamento.carregar()


def _salvar(produtos: list, caminho: str) -> None:
    """
    Persiste a lista de produtos no arquivo JSON.

    Parametros:
        produtos : lista de dicionarios a ser salva
        caminho  : caminho para o arquivo produtos.json

    Lanca:
        OSError: se nao for possivel escrever no caminho informado
    """
    JsonArmazenamento(caminho).salvar(produtos)