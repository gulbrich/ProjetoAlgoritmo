"""
controller.py
-------------
Orquestra os modulos do sistema de precificacao de produtos importados.

Responsabilidades:
    - Receber dados brutos da interfaces (dict)
    - Chamar os modulos de calculo na ordem correta
    - Retornar resultados estruturados para a interfaces
    - Nunca fazer input() ou print()

A interfaces (CLI, GUI ou web) e a unica responsavel por
coletar dados do usuario e exibir resultados.
"""

from modulos.cotacao      import obter_cotacao
from modulos.categorias   import obter_categoria
from modulos.icms         import obter_aliquota
from modulos.impostos     import calcular_todos as calcular_impostos
from modulos.precificacao import calcular_resumo
from modulos.repositorio  import (
    adicionar_produto,
    listar_produtos,
    buscar_por_id,
    buscar_por_nome,
    remover_produto,
)


def calcular_produto(dados: dict) -> dict:
    """
    Executa o calculo completo de impostos e precificacao para um produto.

    Parametros:
        dados (dict) com as chaves obrigatorias:
            nome          : nome do produto (str)
            categoria     : categoria do produto (str, ex: "eletronicos")
            uf_origem     : UF de origem do produto (str, ex: "SP")
            uf_destino    : UF de destino/venda (str, ex: "MG")
            valor_usd     : valor do produto em dolares (float)
            frete         : frete internacional em reais (float)
            despesas      : despesas aduaneiras em reais (float)
            quantidade    : quantidade de unidades (int)
            margem        : margem de lucro desejada, ex: 0.30 (float)

        dados (dict) com a chave opcional:
            cotacao       : cotacao manual do dolar (float)
                            se ausente, busca automaticamente na API

    Retorna:
        dict com as chaves:
            entrada       : dados de entrada utilizados no calculo
            cotacao       : valor da cotacao utilizada
            fonte_cotacao : "API" ou "Manual"
            categoria     : dados da categoria (descricao, aliquotas)
            aliquota_icms : aliquota de ICMS aplicada
            impostos      : resultado de calcular_impostos()
            precificacao  : resultado de calcular_resumo()

    Lanca:
        KeyError  : se alguma chave obrigatoria estiver ausente
        ValueError: se algum valor for invalido
        TypeError : se algum valor for do tipo errado
    """
    _validar_dados_entrada(dados)

    # Cotacao: usa a fornecida ou busca na API
    if "cotacao" in dados and dados["cotacao"] is not None:
        cotacao       = float(dados["cotacao"])
        fonte_cotacao = "Manual"
    else:
        cotacao, fonte_cotacao = obter_cotacao()

    # Aliquotas por categoria
    categoria = obter_categoria(dados["categoria"])

    # Aliquota de ICMS entre os estados
    aliquota_icms = obter_aliquota(dados["uf_origem"], dados["uf_destino"])

    # Calculo dos impostos
    impostos = calcular_impostos(
        valor_usd    = float(dados["valor_usd"]),
        cotacao      = cotacao,
        frete        = float(dados["frete"]),
        aliquota_ii  = categoria["aliquota_ii"],
        aliquota_ipi = categoria["aliquota_ipi"],
        aliquota_icms= aliquota_icms,
        despesas     = float(dados["despesas"]),
    )

    # Precificacao
    precificacao = calcular_resumo(
        custo_total = impostos["custo_total"],
        margem      = float(dados["margem"]),
        quantidade  = int(dados["quantidade"]),
    )

    return {
        "entrada"      : dados,
        "cotacao"      : cotacao,
        "fonte_cotacao": fonte_cotacao,
        "categoria"    : categoria,
        "aliquota_icms": aliquota_icms,
        "impostos"     : impostos,
        "precificacao" : precificacao,
    }


def salvar_produto(nome: str, resultado: dict) -> dict:
    """
    Persiste um produto calculado no repositorio.

    Parametros:
        nome      : nome do produto
        resultado : dicionario retornado por calcular_produto()

    Retorna:
        dict: produto completo com id e data_cadastro
    """
    produto = {
        "nome"        : nome,
        "cotacao"     : resultado["cotacao"],
        "fonte_cotacao": resultado["fonte_cotacao"],
        "categoria"   : resultado["entrada"]["categoria"],
        "uf_origem"   : resultado["entrada"]["uf_origem"],
        "uf_destino"  : resultado["entrada"]["uf_destino"],
        "entrada"     : resultado["entrada"],
        "impostos"    : resultado["impostos"],
        "precificacao": resultado["precificacao"],
    }
    return adicionar_produto(produto)


def consultar_produtos() -> list:
    """
    Retorna todos os produtos cadastrados.

    Retorna:
        list de dicionarios representando os produtos
    """
    return listar_produtos()


def consultar_por_id(id_produto: str) -> dict:
    """
    Busca um produto cadastrado pelo ID.

    Parametros:
        id_produto : ID do produto (ex: "001")

    Retorna:
        dict com os dados do produto

    Lanca:
        ValueError: se o produto nao for encontrado
    """
    return buscar_por_id(id_produto)


def consultar_por_nome(nome: str) -> list:
    """
    Busca produtos cujo nome contenha o termo informado.

    Parametros:
        nome : termo de busca (case-insensitive)

    Retorna:
        list de dicionarios com os produtos encontrados
    """
    return buscar_por_nome(nome)


def excluir_produto(id_produto: str) -> None:
    """
    Remove um produto do repositorio pelo ID.

    Parametros:
        id_produto : ID do produto a remover

    Lanca:
        ValueError: se o produto nao for encontrado
    """
    remover_produto(id_produto)


def _validar_dados_entrada(dados: dict) -> None:
    """
    Valida as chaves obrigatorias e tipos basicos dos dados de entrada.

    Parametros:
        dados : dicionario de entrada a ser validado

    Lanca:
        KeyError  : se alguma chave obrigatoria estiver ausente
        ValueError: se nome estiver vazio ou margem fora do intervalo
        TypeError : se valor_usd, frete, despesas ou margem nao forem numericos
    """
    obrigatorias = [
        "nome", "categoria", "uf_origem", "uf_destino",
        "valor_usd", "frete", "despesas", "quantidade", "margem",
    ]
    for chave in obrigatorias:
        if chave not in dados:
            raise KeyError(f"Campo obrigatorio ausente: '{chave}'.")

    if not str(dados["nome"]).strip():
        raise ValueError("O campo 'nome' nao pode estar vazio.")

    for campo in ["valor_usd", "frete", "despesas", "margem"]:
        if not isinstance(dados[campo], (int, float)):
            raise TypeError(
                f"'{campo}' deve ser numerico, recebido: {type(dados[campo]).__name__}."
            )

    if not isinstance(dados["quantidade"], int):
        raise TypeError(
            f"'quantidade' deve ser inteiro, recebido: {type(dados['quantidade']).__name__}."
        )