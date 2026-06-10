"""
categorias.py
-------------
Interface publica para consulta de categorias de produtos importados.

O controller deve usar apenas este modulo. A fonte de dados atual e JSON,
definida em categorias_json.py. Para trocar a fonte, substitua o import
abaixo sem alterar este arquivo nem o controller.
"""

import os
from modulos.categorias_json import _carregar

_CAMINHO_PADRAO = os.path.join(
    os.path.dirname(__file__), "..", "dados", "categorias.json"
)


def obter_categoria(nome: str, caminho: str = _CAMINHO_PADRAO) -> dict:
    """
    Retorna os dados de uma categoria pelo nome.

    Parametros:
        nome    : nome da categoria (case-insensitive)
        caminho : caminho para o arquivo de categorias (opcional)

    Retorna:
        dict com 'descricao', 'aliquota_ii', 'aliquota_ipi'

    Lanca:
        ValueError: se a categoria nao existir
    """
    categorias = _carregar(caminho)
    chave = nome.strip().lower()
    if chave not in categorias:
        disponiveis = ", ".join(sorted(categorias.keys()))
        raise ValueError(
            f"Categoria '{nome}' nao encontrada. "
            f"Disponiveis: {disponiveis}."
        )
    return categorias[chave]


def listar_categorias(caminho: str = _CAMINHO_PADRAO) -> list:
    """
    Retorna lista ordenada de tuplas (categoria, descricao) para menus.

    Parametros:
        caminho : caminho para o arquivo de categorias (opcional)

    Retorna:
        list de tuplas: [("alimentos", "Alimentos e bebidas"), ...]
    """
    categorias = _carregar(caminho)
    return sorted(
        [(chave, dados["descricao"]) for chave, dados in categorias.items()]
    )