"""
cotacao.py
----------
Busca a cotação atual do dólar (USD -> BRL) via AwesomeAPI.
"""

import requests

URL_API = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
TIMEOUT = 5


def obter_cotacao() -> float:
    """
    Retorna a cotação de compra do dólar (float).

    Lança:
        ConnectionError: se a API estiver inacessível ou sem resposta
        ValueError: se a resposta vier em formato inesperado
    """
    try:
        resposta = requests.get(URL_API, timeout=TIMEOUT)
        resposta.raise_for_status()
        return float(resposta.json()["USDBRL"]["bid"])
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Sem conexão com a internet.")
    except requests.exceptions.Timeout:
        raise ConnectionError(f"API não respondeu em {TIMEOUT} segundos.")
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"Erro HTTP: {e}")
    except (KeyError, ValueError):
        raise ValueError("Resposta da API em formato inesperado.")