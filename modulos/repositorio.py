"""
repositorio.py
--------------
Interface publica para cadastro e consulta de produtos.

O controller deve usar apenas este modulo. A fonte de dados atual e JSON,
definida em repositorio_json.py. Para trocar a fonte (ex: SQLite),
substitua o import abaixo sem alterar este arquivo nem o controller.
"""

import os
from datetime import datetime
from modulos.repositorio_json import _carregar, _salvar

_CAMINHO_PADRAO = os.path.join(
    os.path.dirname(__file__), "..", "dados", "produtos.json"
)


def adicionar_produto(produto: dict,
                      caminho: str = _CAMINHO_PADRAO) -> dict:
    """
    Adiciona um produto ao cadastro e persiste os dados.

    Gera automaticamente um ID sequencial e registra a data de cadastro.

    Parametros:
        produto : dicionario com os dados do produto (sem 'id' e sem 'data_cadastro')
        caminho : caminho para o arquivo de persistencia (opcional)

    Retorna:
        dict: produto completo com 'id' e 'data_cadastro' adicionados

    Lanca:
        ValueError: se o produto nao contiver o campo 'nome'
    """
    if "nome" not in produto or not str(produto["nome"]).strip():
        raise ValueError("O produto deve conter o campo 'nome' preenchido.")

    produtos = _carregar(caminho)

    proximo_id = str(len(produtos) + 1).zfill(3)
    produto_completo = {
        "id"           : proximo_id,
        "data_cadastro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **produto,
    }

    produtos.append(produto_completo)
    _salvar(produtos, caminho)
    return produto_completo


def listar_produtos(caminho: str = _CAMINHO_PADRAO) -> list:
    """
    Retorna todos os produtos cadastrados.

    Parametros:
        caminho : caminho para o arquivo de persistencia (opcional)

    Retorna:
        list de dicionarios representando os produtos
    """
    return _carregar(caminho)


def buscar_por_id(id_produto: str,
                  caminho: str = _CAMINHO_PADRAO) -> dict:
    """
    Busca um produto pelo ID.

    Parametros:
        id_produto : ID do produto (ex: "001")
        caminho    : caminho para o arquivo de persistencia (opcional)

    Retorna:
        dict com os dados do produto

    Lanca:
        ValueError: se o produto nao for encontrado
    """
    produtos = _carregar(caminho)
    for p in produtos:
        if p.get("id") == id_produto.strip():
            return p
    raise ValueError(f"Produto com ID '{id_produto}' nao encontrado.")


def buscar_por_nome(nome: str,
                    caminho: str = _CAMINHO_PADRAO) -> list:
    """
    Busca produtos cujo nome contenha o termo informado (case-insensitive).

    Parametros:
        nome    : termo de busca
        caminho : caminho para o arquivo de persistencia (opcional)

    Retorna:
        list de dicionarios com os produtos encontrados (pode ser vazia)
    """
    termo = nome.strip().lower()
    produtos = _carregar(caminho)
    return [p for p in produtos if termo in p.get("nome", "").lower()]


def remover_produto(id_produto: str,
                    caminho: str = _CAMINHO_PADRAO) -> None:
    """
    Remove um produto do cadastro pelo ID.

    Parametros:
        id_produto : ID do produto a remover
        caminho    : caminho para o arquivo de persistencia (opcional)

    Lanca:
        ValueError: se o produto nao for encontrado
    """
    produtos = _carregar(caminho)
    filtrados = [p for p in produtos if p.get("id") != id_produto.strip()]

    if len(filtrados) == len(produtos):
        raise ValueError(f"Produto com ID '{id_produto}' nao encontrado.")

    _salvar(filtrados, caminho)