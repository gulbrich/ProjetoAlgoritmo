"""
cotacao.py
----------
Busca a cotacao atual do dolar (USD -> BRL) via AwesomeAPI.
"""

import requests

URL_API = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
TIMEOUT = 5


def obter_cotacao() -> float:
    """
    Retorna a cotacao de compra do dolar (float).

    Lanca:
        ConnectionError: se a API estiver inacessivel ou sem resposta
        ValueError: se a resposta vier em formato inesperado
    """
    try:
        resposta = requests.get(URL_API, timeout=TIMEOUT)
        resposta.raise_for_status()
        return float(resposta.json()["USDBRL"]["bid"])
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Sem conexao com a internet.")
    except requests.exceptions.Timeout:
        raise ConnectionError(f"API nao respondeu em {TIMEOUT} segundos.")
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"Erro HTTP: {e}")
    except (KeyError, ValueError):
        raise ValueError("Resposta da API em formato inesperado.")