"""
categorias.py
-------------
Carrega e consulta a tabela de categorias de produtos importados.

Cada categoria armazena aliquotas representativas de II e IPI.
Em producao, as aliquotas exatas devem ser consultadas pelo codigo
NCM no simulador da Receita Federal (portal.siscomex.gov.br).
"""

import csv
import os

CAMINHO_PADRAO = os.path.join(os.path.dirname(__file__), "..", "dados", "categorias.csv")


def carregar_categorias(caminho: str = CAMINHO_PADRAO) -> dict:
    """
    Carrega o arquivo de categorias e retorna um dicionario indexado
    pela chave 'categoria'.

    Parametros:
        caminho : caminho para o arquivo categorias.csv

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
        ValueError: se o arquivo estiver mal formatado
    """
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo de categorias nao encontrado: {caminho}")

    categorias = {}
    try:
        with open(caminho, newline="", encoding="utf-8") as f:
            for i, linha in enumerate(csv.DictReader(f), start=2):
                chave = linha["categoria"].strip().lower()
                categorias[chave] = {
                    "descricao"   : linha["descricao"].strip(),
                    "aliquota_ii" : float(linha["aliquota_ii"]),
                    "aliquota_ipi": float(linha["aliquota_ipi"]),
                }
    except KeyError as e:
        raise ValueError(f"Coluna ausente no arquivo de categorias: {e}")
    except ValueError:
        raise ValueError(f"Valor invalido na linha {i} do arquivo de categorias.")

    return categorias


def obter_categoria(nome: str, categorias: dict) -> dict:
    """
    Retorna os dados de uma categoria pelo nome.

    Parametros:
        nome       : nome da categoria (case-insensitive)
        categorias : dicionario carregado por carregar_categorias()

    Retorna:
        dict com 'descricao', 'aliquota_ii', 'aliquota_ipi'

    Lanca:
        ValueError: se a categoria nao existir
    """
    chave = nome.strip().lower()
    if chave not in categorias:
        disponiveis = ", ".join(sorted(categorias.keys()))
        raise ValueError(
            f"Categoria '{nome}' nao encontrada. "
            f"Categorias disponiveis: {disponiveis}."
        )
    return categorias[chave]


def listar_categorias(categorias: dict) -> list:
    """
    Retorna uma lista ordenada de tuplas (categoria, descricao)
    para exibicao em menus.

    Parametros:
        categorias : dicionario carregado por carregar_categorias()

    Retorna:
        list de tuplas: [("alimentos", "Alimentos e bebidas"), ...]
    """
    return sorted(
        [(chave, dados["descricao"]) for chave, dados in categorias.items()]
    )