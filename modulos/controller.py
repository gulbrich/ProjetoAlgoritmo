"""
controller.py
-------------
Orquestra os módulos do sistema de precificação de produtos importados.

Responsabilidades:
    - Receber dados brutos da interface (dict)
    - Chamar os módulos de cálculo na ordem correta
    - Retornar resultados estruturados para a interface
    - Nunca fazer input() ou print()

A interface (CLI, GUI ou web) é a única responsável por
coletar dados do usuário e exibir resultados.
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
    Executa o cálculo completo de impostos e precificação para um produto.

    Parâmetros:
        dados (dict) com as chaves obrigatórias:
            nome          : nome do produto (str)
            categoria     : categoria do produto (str, ex: "eletronicos")
            uf_origem     : UF de origem do produto (str, ex: "SP")
            uf_destino    : UF de destino/venda (str, ex: "MG")
            valor_usd     : valor do produto em dólares (float)
            frete         : frete internacional em reais (float)
            despesas      : despesas aduaneiras em reais (float)
            quantidade    : quantidade de unidades (int)
            margem        : margem de lucro desejada, ex: 0.30 (float)

        dados (dict) com a chave opcional:
            cotacao       : cotação manual do dólar (float)
                            se ausente, busca automaticamente na API

    Retorna:
        dict com as chaves:
            entrada       : dados de entrada utilizados no cálculo
            cotacao       : valor da cotação utilizada
            fonte_cotacao : "API" ou "Manual"
            categoria     : dados da categoria (descrição, alíquotas)
            aliquota_icms : alíquota de ICMS aplicada
            impostos      : resultado de calcular_impostos()
            precificacao  : resultado de calcular_resumo()

    Lança:
        KeyError  : se alguma chave obrigatória estiver ausente
        ValueError: se algum valor for inválido
        TypeError : se algum valor for do tipo errado
    """
    _validar_dados_entrada(dados)

    # Cotação: usa a fornecida ou busca na API
    if "cotacao" in dados and dados["cotacao"] is not None:
        cotacao       = float(dados["cotacao"])
        fonte_cotacao = dados.get("fonte_cotacao", "Manual")
    else:
        cotacao, fonte_cotacao = obter_cotacao()

    # Alíquotas por categoria ou NCM
    # Se categoria_dados já foi fornecido (busca por NCM), usa diretamente
    if "categoria_dados" in dados and dados["categoria_dados"]:
        categoria = dados["categoria_dados"]
    else:
        categoria = obter_categoria(dados["categoria"])

    # Alíquota de ICMS entre os estados
    aliquota_icms = obter_aliquota(dados["uf_origem"], dados["uf_destino"])

    # Cálculo dos impostos — frete e despesas são rateados por unidade internamente
    impostos = calcular_impostos(
        valor_usd    = float(dados["valor_usd"]),
        cotacao      = cotacao,
        frete        = float(dados["frete"]),
        aliquota_ii  = categoria["aliquota_ii"],
        aliquota_ipi = categoria["aliquota_ipi"],
        aliquota_icms= aliquota_icms,
        despesas     = float(dados["despesas"]),
        quantidade   = int(dados["quantidade"]),
    )

    # Precificação
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
    Persiste um produto calculado no repositório.

    Parâmetros:
        nome      : nome do produto
        resultado : dicionário retornado por calcular_produto()

    Retorna:
        dict: produto completo com id e data_cadastro
    """
    produto = {
        "nome"          : nome,
        "cotacao"       : resultado["cotacao"],
        "fonte_cotacao" : resultado["fonte_cotacao"],
        "categoria"     : resultado["entrada"]["categoria"],
        "categoria_dados": resultado["categoria"],  # dict com aliquota_ii, aliquota_ipi
        "uf_origem"     : resultado["entrada"]["uf_origem"],
        "uf_destino"    : resultado["entrada"]["uf_destino"],
        "entrada"       : resultado["entrada"],
        "impostos"      : resultado["impostos"],
        "precificacao"  : resultado["precificacao"],
    }
    return adicionar_produto(produto)


def consultar_produtos() -> list:
    """
    Retorna todos os produtos cadastrados.

    Retorna:
        list de dicionários representando os produtos
    """
    return listar_produtos()


def consultar_por_id(id_produto: str) -> dict:
    """
    Busca um produto cadastrado pelo ID.

    Parâmetros:
        id_produto : ID do produto (ex: "001")

    Retorna:
        dict com os dados do produto

    Lança:
        ValueError: se o produto não for encontrado
    """
    return buscar_por_id(id_produto)


def consultar_por_nome(nome: str) -> list:
    """
    Busca produtos cujo nome contenha o termo informado.

    Parâmetros:
        nome : termo de busca (case-insensitive)

    Retorna:
        list de dicionários com os produtos encontrados
    """
    return buscar_por_nome(nome)


def excluir_produto(id_produto: str) -> None:
    """
    Remove um produto do repositório pelo ID.

    Parâmetros:
        id_produto : ID do produto a remover

    Lança:
        ValueError: se o produto não for encontrado
    """
    remover_produto(id_produto)


def _validar_dados_entrada(dados: dict) -> None:
    """
    Valida as chaves obrigatórias e tipos básicos dos dados de entrada.

    Parâmetros:
        dados : dicionário de entrada a ser validado

    Lança:
        KeyError  : se alguma chave obrigatória estiver ausente
        ValueError: se nome estiver vazio ou margem fora do intervalo
        TypeError : se valor_usd, frete, despesas ou margem não forem numéricos
    """
    obrigatorias = [
        "nome", "categoria", "uf_origem", "uf_destino",
        "valor_usd", "frete", "despesas", "quantidade", "margem",
    ]
    for chave in obrigatorias:
        if chave not in dados:
            raise KeyError(f"Campo obrigatório ausente: '{chave}'.")

    if not str(dados["nome"]).strip():
        raise ValueError("O campo 'nome' não pode estar vazio.")

    for campo in ["valor_usd", "frete", "despesas", "margem"]:
        if not isinstance(dados[campo], (int, float)):
            raise TypeError(
                f"'{campo}' deve ser numérico, recebido: {type(dados[campo]).__name__}."
            )

    if not isinstance(dados["quantidade"], int):
        raise TypeError(
            f"'quantidade' deve ser inteiro, recebido: {type(dados['quantidade']).__name__}."
        )