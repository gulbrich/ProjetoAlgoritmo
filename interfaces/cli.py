"""
cli.py
------
Interface de linha de comando do sistema de precificacao de produtos importados.

E a unica camada do sistema que realiza input() e print().
Coleta dados do usuario, chama o controller e exibe os resultados.
"""

from modulos.controller  import (
    calcular_produto,
    salvar_produto,
    consultar_produtos,
    consultar_por_id,
    consultar_por_nome,
    excluir_produto,
)
from modulos.categorias  import listar_categorias
from modulos.icms        import listar_ufs
from modulos.cotacao     import obter_cotacao
from interfaces.graficos import (
    composicao_custo,
    comparativo_produtos,
    comparativo_estados,
)


# ---------------------------------------------------------------------------
# Utilitarios de entrada
# ---------------------------------------------------------------------------

def _ler_float(mensagem: str, minimo: float = 0.0) -> float:
    """Le um numero float do usuario, validando que seja >= minimo."""
    while True:
        try:
            valor = float(input(mensagem).strip().replace(",", "."))
            if valor < minimo:
                print(f"  Valor deve ser maior ou igual a {minimo}.")
                continue
            return valor
        except ValueError:
            print("  Entrada invalida. Digite um numero (ex: 1500.00).")


def _ler_int(mensagem: str, minimo: int = 1) -> int:
    """Le um numero inteiro do usuario, validando que seja >= minimo."""
    while True:
        try:
            valor = int(input(mensagem).strip())
            if valor < minimo:
                print(f"  Valor deve ser maior ou igual a {minimo}.")
                continue
            return valor
        except ValueError:
            print("  Entrada invalida. Digite um numero inteiro.")


def _ler_uf(mensagem: str, padrao: str = "SP") -> str:
    """
    Le uma UF valida do usuario.
    Se vazio, usa o padrao informado e avisa o usuario.
    """
    ufs = set(listar_ufs())
    while True:
        uf = input(mensagem).strip().upper()
        if uf == "":
            print(f"  Nenhum estado informado. Usando padrao: {padrao}.")
            return padrao
        if uf in ufs:
            return uf
        print("  UF invalida. Use a sigla de dois caracteres (ex: SP, MG, RJ).")


def _ler_float_opcional(mensagem: str, padrao: float = 0.0) -> float:
    """
    Le um numero float do usuario.
    Se vazio, retorna o valor padrao sem avisar (campo opcional).
    """
    while True:
        entrada = input(mensagem).strip().replace(",", ".")
        if entrada == "":
            return padrao
        try:
            valor = float(entrada)
            if valor < 0:
                print("  Valor nao pode ser negativo.")
                continue
            return valor
        except ValueError:
            print("  Entrada invalida. Digite um numero ou deixe vazio.")


def _ler_int_opcional(mensagem: str, padrao: int = 1) -> int:
    """
    Le um numero inteiro do usuario.
    Se vazio, retorna o valor padrao sem avisar (campo opcional).
    """
    while True:
        entrada = input(mensagem).strip()
        if entrada == "":
            return padrao
        try:
            valor = int(entrada)
            if valor < 1:
                print("  Valor deve ser maior ou igual a 1.")
                continue
            return valor
        except ValueError:
            print("  Entrada invalida. Digite um numero inteiro ou deixe vazio.")


def _ler_categoria(mensagem: str) -> str:
    """Exibe as categorias disponiveis e le uma escolha por numero."""
    categorias = listar_categorias()
    print("\n  Categorias disponiveis:")
    for i, (chave, descricao) in enumerate(categorias, start=1):
        print(f"    {i:>2}. {descricao}")
    while True:
        try:
            numero = int(input(mensagem).strip())
            if 1 <= numero <= len(categorias):
                return categorias[numero - 1][0]
            print(f"  Numero invalido. Digite entre 1 e {len(categorias)}.")
        except ValueError:
            print(f"  Entrada invalida. Digite um numero entre 1 e {len(categorias)}.")


def _ler_confirmacao(mensagem: str) -> bool:
    """Le uma confirmacao s/n do usuario."""
    while True:
        resposta = input(mensagem).strip().lower()
        if resposta in ("s", "sim"):
            return True
        if resposta in ("n", "nao", "nao"):
            return False
        print("  Responda com 's' ou 'n'.")


def _obter_cotacao_com_fallback() -> tuple:
    """
    Tenta buscar a cotacao do dolar via API.
    Se falhar, solicita a cotacao manualmente ao usuario.

    Retorna:
        tuple: (cotacao: float, fonte: str)
    """
    print("\n  Buscando cotacao do dolar...")
    try:
        cotacao = obter_cotacao()
        print(f"  Cotacao obtida via API: R$ {cotacao:.4f}")
        return cotacao, "API"
    except (ConnectionError, ValueError) as e:
        print(f"  Nao foi possivel obter a cotacao automatica: {e}")
        print("  Informe a cotacao manualmente.")
        cotacao = _ler_float("  Cotacao do dolar (R$/USD): R$ ", minimo=0.01)
        return cotacao, "Manual"


# ---------------------------------------------------------------------------
# Utilitarios de exibicao
# ---------------------------------------------------------------------------

def _separador(char: str = "-", largura: int = 56) -> None:
    print(f"  {char * largura}")


def _exibir_resultado(resultado: dict) -> None:
    """Exibe o resultado completo de um calculo de precificacao."""
    imp  = resultado["impostos"]
    prec = resultado["precificacao"]
    ent  = resultado["entrada"]

    _separador("=")
    print(f"  RESULTADO DO CALCULO")
    _separador("=")
    print(f"  Produto          : {ent['nome']}")
    print(f"  Categoria        : {resultado['categoria']['descricao']}")
    print(f"  Origem -> Destino: {ent['uf_origem']} -> {ent['uf_destino']}")
    print(f"  Cotacao do dolar : R$ {resultado['cotacao']:.4f}  ({resultado['fonte_cotacao']})")
    _separador()
    print(f"  COMPOSICAO DO CUSTO")
    _separador()
    print(f"  Valor aduaneiro  : R$ {imp['valor_aduaneiro']:>12,.2f}")
    print(f"  II               : R$ {imp['ii']:>12,.2f}  ({resultado['categoria']['aliquota_ii']*100:.0f}%)")
    print(f"  IPI              : R$ {imp['ipi']:>12,.2f}  ({resultado['categoria']['aliquota_ipi']*100:.0f}%)")
    print(f"  PIS              : R$ {imp['pis']:>12,.2f}  (2,10%)")
    print(f"  COFINS           : R$ {imp['cofins']:>12,.2f}  (9,65%)")
    print(f"  ICMS             : R$ {imp['icms']:>12,.2f}  ({resultado['aliquota_icms']*100:.0f}%)")
    print(f"  Despesas         : R$ {imp['despesas']:>12,.2f}")
    _separador()
    print(f"  Total impostos   : R$ {imp['total_impostos']:>12,.2f}")
    print(f"  Custo unitario   : R$ {prec['custo_unitario']:>12,.2f}")
    _separador()
    print(f"  PRECIFICACAO  ({ent['margem']*100:.0f}% de margem)")
    _separador()
    print(f"  Preco de venda   : R$ {prec['preco_venda']:>12,.2f}")
    print(f"  Lucro unitario   : R$ {prec['lucro_unitario']:>12,.2f}")
    print(f"  Quantidade       : {prec['quantidade']:>15} un.")
    print(f"  Receita total    : R$ {prec['receita_total']:>12,.2f}")
    print(f"  Lucro do lote    : R$ {prec['lucro_total_lote']:>12,.2f}")
    _separador("=")


def _exibir_lista_produtos(produtos: list) -> None:
    """Exibe a lista de produtos cadastrados em formato de tabela."""
    if not produtos:
        print("\n  Nenhum produto cadastrado.")
        return
    _separador("=")
    print(f"  {'ID':<5} {'Nome':<28} {'Categoria':<15} {'Preco de venda':>15}")
    _separador()
    for p in produtos:
        print(
            f"  {p['id']:<5} "
            f"{p['nome'][:27]:<28} "
            f"{p['categoria']:<15} "
            f"R$ {p['precificacao']['preco_venda']:>12,.2f}"
        )
    _separador("=")


def _produto_para_resultado(produto: dict) -> dict:
    """
    Reconstroi o dicionario de resultado a partir de um produto cadastrado,
    no formato esperado por _exibir_resultado() e pelas funcoes de graficos.
    """
    return {
        "entrada"      : produto["entrada"],
        "cotacao"      : produto["cotacao"],
        "fonte_cotacao": produto["fonte_cotacao"],
        "categoria"    : produto["entrada"],
        "aliquota_icms": produto["impostos"]["icms"] / produto["impostos"]["valor_aduaneiro"],
        "impostos"     : produto["impostos"],
        "precificacao" : produto["precificacao"],
    }


# ---------------------------------------------------------------------------
# Telas
# ---------------------------------------------------------------------------

def tela_calcular_produto() -> None:
    """Coleta dados, executa o calculo e oferece salvar o produto."""
    print("\n  NOVO CALCULO DE PRECIFICACAO")
    _separador()

    cotacao, fonte_cotacao = _obter_cotacao_com_fallback()

    dados = {
        "nome"         : input("\n  Nome do produto   : ").strip(),
        "categoria"    : _ler_categoria("  Categoria (numero): "),
        "uf_origem"    : _ler_uf("  UF de origem      [Enter=SP]: "),
        "uf_destino"   : _ler_uf("  UF de destino     [Enter=SP]: "),
        "valor_usd"    : _ler_float("  Valor em USD      : $ ", minimo=0.01),
        "frete"        : _ler_float_opcional("  Frete (R$)        [Enter=0]: R$ "),
        "despesas"     : _ler_float_opcional("  Despesas (R$)     [Enter=0]: R$ "),
        "quantidade"   : _ler_int_opcional("  Quantidade (un.)  [Enter=1]: "),
        "margem"       : _ler_float("  Margem de lucro % : ", minimo=1) / 100,
        "cotacao"      : cotacao,
        "fonte_cotacao": fonte_cotacao,
    }

    try:
        resultado = calcular_produto(dados)
        _exibir_resultado(resultado)

        if _ler_confirmacao("\n  Deseja salvar este produto? (s/n): "):
            salvo = salvar_produto(dados["nome"], resultado)
            print(f"\n  Produto salvo com ID {salvo['id']}.")

        if _ler_confirmacao("\n  Deseja ver o grafico de composicao do custo? (s/n): "):
            composicao_custo(resultado)

    except (ValueError, TypeError, KeyError) as e:
        print(f"\n  Erro ao calcular: {e}")


def tela_listar_produtos() -> None:
    """Exibe todos os produtos cadastrados."""
    print("\n  PRODUTOS CADASTRADOS")
    _exibir_lista_produtos(consultar_produtos())


def tela_buscar_produto() -> None:
    """Busca um produto por ID ou nome e exibe seus detalhes."""
    print("\n  BUSCAR PRODUTO")
    _separador()
    print("  1. Buscar por ID")
    print("  2. Buscar por nome")
    opcao = input("\n  Opcao: ").strip()

    try:
        if opcao == "1":
            id_produto = input("  ID do produto: ").strip()
            produto = consultar_por_id(id_produto)
            _exibir_resultado(_produto_para_resultado(produto))
        elif opcao == "2":
            nome = input("  Nome (ou parte): ").strip()
            _exibir_lista_produtos(consultar_por_nome(nome))
        else:
            print("  Opcao invalida.")
    except ValueError as e:
        print(f"\n  {e}")


def tela_remover_produto() -> None:
    """Remove um produto pelo ID apos confirmacao."""
    print("\n  REMOVER PRODUTO")
    _separador()
    tela_listar_produtos()
    id_produto = input("\n  ID do produto a remover: ").strip()

    try:
        produto = consultar_por_id(id_produto)
        if _ler_confirmacao(f"  Confirma remocao de '{produto['nome']}'? (s/n): "):
            excluir_produto(id_produto)
            print("  Produto removido.")
        else:
            print("  Operacao cancelada.")
    except ValueError as e:
        print(f"\n  {e}")


# ---------------------------------------------------------------------------
# Tela de graficos
# ---------------------------------------------------------------------------

def tela_graficos() -> None:
    """Menu de graficos. Requer ao menos um produto cadastrado."""
    produtos = consultar_produtos()
    if not produtos:
        print("\n  Nenhum produto cadastrado. Cadastre ao menos um produto primeiro.")
        return

    while True:
        print("\n  GRAFICOS")
        _separador()
        print("  1. Composicao do custo (pizza)")
        print("  2. Comparativo entre produtos (barras empilhadas)")
        print("  3. Ponto de equilibrio")
        print("  4. Comparativo por estado de destino")
        print("  0. Voltar")
        _separador()

        opcao = input("  Opcao: ").strip()

        if opcao == "0":
            break

        elif opcao == "1":
            _exibir_lista_produtos(produtos)
            id_produto = input("\n  ID do produto: ").strip()
            try:
                produto = consultar_por_id(id_produto)
                composicao_custo(_produto_para_resultado(produto))
            except ValueError as e:
                print(f"\n  {e}")

        elif opcao == "2":
            if len(produtos) < 2:
                print("\n  Necessario ao menos 2 produtos cadastrados para comparar.")
                continue
            _exibir_lista_produtos(produtos)
            print("\n  Informe os IDs dos produtos a comparar (separados por virgula):")
            entrada = input("  IDs: ").strip()
            ids = [i.strip() for i in entrada.split(",")]
            try:
                resultados = [_produto_para_resultado(consultar_por_id(i)) for i in ids]
                comparativo_produtos(resultados)
            except ValueError as e:
                print(f"\n  {e}")

        elif opcao == "3":
            _exibir_lista_produtos(produtos)
            id_produto = input("\n  ID do produto: ").strip()
            try:
                produto = consultar_por_id(id_produto)
                print("  Informe as UFs a comparar (separadas por virgula, ex: SP,MG,BA,RS):")
                entrada = input("  UFs: ").strip().upper()
                estados = [uf.strip() for uf in entrada.split(",")]
                comparativo_estados(_produto_para_resultado(produto), estados, calcular_produto)
            except ValueError as e:
                print(f"\n  {e}")

        else:
            print("  Opcao invalida.")


# ---------------------------------------------------------------------------
# Menu principal
# ---------------------------------------------------------------------------

def menu() -> None:
    """Exibe o menu principal e gerencia a navegacao."""
    while True:
        print("\n" + "=" * 60)
        print("  SISTEMA DE PRECIFICACAO DE PRODUTOS IMPORTADOS")
        print("=" * 60)
        print("  1. Novo calculo de precificacao")
        print("  2. Listar produtos cadastrados")
        print("  3. Buscar produto")
        print("  4. Remover produto")
        print("  5. Graficos")
        print("  0. Sair")
        print("=" * 60)

        opcao = input("  Opcao: ").strip()

        if opcao == "1":
            tela_calcular_produto()
        elif opcao == "2":
            tela_listar_produtos()
        elif opcao == "3":
            tela_buscar_produto()
        elif opcao == "4":
            tela_remover_produto()
        elif opcao == "5":
            tela_graficos()
        elif opcao == "0":
            print("\n  Encerrando o sistema.")
            break
        else:
            print("\n  Opcao invalida. Tente novamente.")