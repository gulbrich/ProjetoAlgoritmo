import os
import json
import requests

URL_BRASILAPI   = "https://brasilapi.com.br/api/ncm/v1"
TIMEOUT         = 8
_CAMINHO_NCM       = os.path.join(os.path.dirname(__file__), "..", "dados", "ncm.json")
_CAMINHO_CAPITULOS = os.path.join(os.path.dirname(__file__), "..", "dados", "ncm_capitulos.json")


def _carregar_tabela_local() -> dict:
    """
    Carrega a tabela de NCMs do arquivo dados/ncm.json.

    Retorna:
        dict no formato: {codigo: (descricao, aliquota_ii, aliquota_ipi)}

    Lança:
        FileNotFoundError: se o arquivo não for encontrado
        ValueError: se o arquivo estiver corrompido
    """
    if not os.path.exists(_CAMINHO_NCM):
        raise FileNotFoundError(
            f"Arquivo de NCMs não encontrado: {_CAMINHO_NCM}"
        )
    try:
        with open(_CAMINHO_NCM, encoding="utf-8") as f:
            dados = json.load(f)
        return {
            cod: (item["descricao"], item["aliquota_ii"], item["aliquota_ipi"])
            for cod, item in dados.items()
        }
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Arquivo ncm.json corrompido: {e}")


def _carregar_capitulos() -> dict:
    """
    Carrega a tabela de alíquotas de II por capítulo NCM
    do arquivo dados/ncm_capitulos.json.

    Retorna:
        dict no formato: {"87": 0.35, "85": 0.16, ...}

    Lança:
        FileNotFoundError: se o arquivo não for encontrado
        ValueError: se o arquivo estiver corrompido
    """
    if not os.path.exists(_CAMINHO_CAPITULOS):
        raise FileNotFoundError(
            f"Arquivo de capítulos NCM não encontrado: {_CAMINHO_CAPITULOS}"
        )
    try:
        with open(_CAMINHO_CAPITULOS, encoding="utf-8") as f:
            dados = json.load(f)
        return {cap: item["aliquota_ii"] for cap, item in dados.items()}
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Arquivo ncm_capitulos.json corrompido: {e}")


# Carregados uma vez ao importar o módulo
TABELA_LOCAL = _carregar_tabela_local()
TABELA_CAPITULOS = _carregar_capitulos()



def buscar_ncm_api(termo: str) -> list:
    """
    Busca NCMs por descrição na BrasilAPI.

    Parâmetros:
        termo : texto de busca (ex: "celular", "notebook")

    Retorna:
        list de dicts com 'codigo' e 'descricao'

    Lança:
        ConnectionError: se a API estiver inacessível
        ValueError: se a resposta vier em formato inesperado
    """
    try:
        resposta = requests.get(
            URL_BRASILAPI,
            params={"search": termo},
            timeout=TIMEOUT
        )
        resposta.raise_for_status()
        dados = resposta.json()
        return [
            {"codigo": item["codigo"], "descricao": item["descricao"]}
            for item in dados
        ]
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Sem conexão com a internet.")
    except requests.exceptions.Timeout:
        raise ConnectionError(f"API não respondeu em {TIMEOUT} segundos.")
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"Erro HTTP na API de NCM: {e}")
    except (KeyError, ValueError):
        raise ValueError("Resposta da API de NCM em formato inesperado.")


def buscar_ncm_local(termo: str) -> list:
    """
    Busca NCMs por descrição na tabela local (offline).

    Parâmetros:
        termo : texto de busca (case-insensitive)

    Retorna:
        list de dicts com 'codigo' e 'descricao'
    """
    termo_lower = termo.strip().lower()
    return [
        {
            "codigo"      : codigo,
            "descricao"   : descricao,
            "aliquota_ii" : ii,
            "aliquota_ipi": ipi,
        }
        for codigo, (descricao, ii, ipi) in TABELA_LOCAL.items()
        if termo_lower in descricao.lower() or termo_lower in codigo.lower()
    ]


def buscar_ncm(termo: str) -> list:
    """
    Busca NCMs por descrição — tenta a API primeiro, usa tabela local como fallback.

    Parâmetros:
        termo : texto de busca

    Retorna:
        list de dicts com 'codigo', 'descricao' e 'fonte'
    """
    try:
        resultados = buscar_ncm_api(termo)
        for r in resultados:
            r["fonte"] = "BrasilAPI"
        return resultados
    except (ConnectionError, ValueError):
        resultados = buscar_ncm_local(termo)
        for r in resultados:
            r["fonte"] = "Local"
        return resultados


def buscar_aliquotas_por_codigo(codigo: str) -> dict:
    """
    Busca as alíquotas de IPI de um NCM específico na BrasilAPI
    e estima o II pelo capítulo NCM (tabela TEC).

    Parâmetros:
        codigo : código NCM (ex: "8709.11.00" ou "87091100")

    Retorna:
        dict com 'codigo', 'descricao', 'aliquota_ii', 'aliquota_ipi', 'fonte'

    Lança:
        ConnectionError: se a API estiver inacessível
        ValueError: se o NCM não for encontrado na API
    """
    codigo_norm = codigo.replace(".", "").replace(" ", "")
    try:
        resposta = requests.get(
            f"{URL_BRASILAPI}/{codigo_norm}",
            timeout=TIMEOUT
        )
        resposta.raise_for_status()
        dados = resposta.json()

        ipi = float(dados.get("aliq_ipi", 0) or 0) / 100
        ii  = _estimar_ii_por_capitulo(codigo_norm[:2])

        return {
            "codigo"      : dados.get("codigo", codigo),
            "descricao"   : dados.get("descricao", ""),
            "aliquota_ii" : ii,
            "aliquota_ipi": ipi,
            "fonte"       : "BrasilAPI",
        }
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Sem conexão com a internet.")
    except requests.exceptions.Timeout:
        raise ConnectionError(f"API não respondeu em {TIMEOUT} segundos.")
    except requests.exceptions.HTTPError:
        raise ValueError(f"NCM '{codigo}' não encontrado na BrasilAPI.")
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"Erro ao processar resposta da API: {e}")


def _estimar_ii_por_capitulo(capitulo: str) -> float:
    """
    Estima a alíquota de II pelo capítulo NCM com base na TEC (Tarifa Externa Comum).
    Os valores são carregados do arquivo dados/ncm_capitulos.json.

    Parâmetros:
        capitulo : dois primeiros dígitos do NCM (ex: "87" para veículos)

    Retorna:
        float: alíquota estimada de II (0.14 como fallback se não encontrado)
    """
    return TABELA_CAPITULOS.get(capitulo, 0.14)


def obter_aliquotas_ncm(codigo: str) -> dict:
    """
    Retorna as alíquotas de II e IPI para um código NCM.

    Consulta primeiro a tabela local. Se não encontrar,
    tenta buscar na BrasilAPI. Se offline, lança ValueError.

    Parâmetros:
        codigo : código NCM (com ou sem pontos, ex: "8517.12.31" ou "85171231")

    Retorna:
        dict com 'codigo', 'descricao', 'aliquota_ii', 'aliquota_ipi'

    Lança:
        ValueError: se o NCM não for encontrado em nenhuma fonte
        ConnectionError: se a API estiver inacessível e NCM não estiver na tabela local
    """
    codigo_norm = codigo.replace(".", "").replace(" ", "")

    # Tenta tabela local primeiro
    for cod, (descricao, ii, ipi) in TABELA_LOCAL.items():
        if cod.replace(".", "") == codigo_norm:
            return {
                "codigo"      : cod,
                "descricao"   : descricao,
                "aliquota_ii" : ii,
                "aliquota_ipi": ipi,
                "fonte"       : "Local",
            }

    # Tenta BrasilAPI pelo código específico
    return buscar_aliquotas_por_codigo(codigo)