"""
armazenamento.py
----------------
Classe utilitaria para persistencia de dados em JSON.

Define a interfaces abstrata BaseArmazenamento, que pode ser implementada
para qualquer tipo de banco de dados (JSON, SQLite, PostgreSQL, etc).

O controller e os modulos de dados dependem apenas de BaseArmazenamento,
nunca de JsonArmazenamento diretamente — garantindo desacoplamento total.

Troca de banco de dados:
    1. Crie uma nova classe que herde BaseArmazenamento
    2. Implemente os metodos carregar() e salvar()
    3. Substitua JsonArmazenamento nos modulos de dados
    O controller e as interfaces nao precisam ser alterados.
"""

import json
import os
from abc import ABC, abstractmethod


class BaseArmazenamento(ABC):
    """
    Interface abstrata para persistencia de dados.

    Qualquer mecanismo de armazenamento deve implementar
    os metodos carregar() e salvar().
    """

    @abstractmethod
    def carregar(self) -> object:
        """
        Le e retorna os dados persistidos.

        Retorna:
            object: dados carregados (dict, list, etc.)
        """

    @abstractmethod
    def salvar(self, dados: object) -> None:
        """
        Persiste os dados fornecidos.

        Parametros:
            dados : objeto a ser persistido (dict, list, etc.)
        """


class JsonArmazenamento(BaseArmazenamento):
    """
    Implementacao de BaseArmazenamento usando arquivos JSON.

    Parametros:
        caminho     : caminho para o arquivo JSON
        valor_padrao: valor retornado se o arquivo nao existir (default: None)
    """

    def __init__(self, caminho: str, valor_padrao: object = None) -> None:
        self._caminho      = caminho
        self._valor_padrao = valor_padrao

    def carregar(self) -> object:
        """
        Le o arquivo JSON e retorna os dados.

        Retorna o valor_padrao se o arquivo nao existir ou estiver vazio.

        Lanca:
            ValueError: se o arquivo existir mas estiver corrompido
        """
        if not os.path.exists(self._caminho):
            return self._valor_padrao

        try:
            with open(self._caminho, encoding="utf-8") as f:
                conteudo = f.read().strip()
                if not conteudo:
                    return self._valor_padrao
                return json.loads(conteudo)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Arquivo corrompido '{self._caminho}': {e}"
            )

    def salvar(self, dados: object) -> None:
        """
        Persiste os dados no arquivo JSON.

        Cria o diretorio pai se nao existir.

        Lanca:
            OSError: se nao for possivel escrever no caminho informado
        """
        os.makedirs(os.path.dirname(self._caminho), exist_ok=True)
        with open(self._caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)