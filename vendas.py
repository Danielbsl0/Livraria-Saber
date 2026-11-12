from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from entradas import solicitar_id
from livros import carregar_livros, salvar_livros
from persistencia import carregar_dados, salvar_dados


NOME_ARQUIVO = "vendas.json"
_CENTAVO = Decimal("0.01")


def _decimal_valido(valor, permitir_zero=True):
    if isinstance(valor, bool) or not isinstance(valor, (int, float, Decimal)):
        return False
    try:
        numero = Decimal(str(valor))
        numero.quantize(_CENTAVO, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return False
    return numero.is_finite() and (numero >= 0 if permitir_zero else numero > 0)


def _valor_monetario(valor):
    """Converte um valor para Decimal limitado a centavos."""
    try:
        return Decimal(str(valor)).quantize(_CENTAVO, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as erro:
        raise ValueError("Valor monetário inválido.") from erro


def _carregar_vendas():
    """Carrega e valida os registros de vendas do arquivo JSON."""
    try:
        vendas = carregar_dados(NOME_ARQUIVO)
        if not isinstance(vendas, list):
            raise ValueError("O arquivo de vendas deve conter uma lista.")

        ids_encontrados = set()
        for venda in vendas:
            if not isinstance(venda, dict):
                raise ValueError("Há um registro de venda inválido no arquivo.")
            if any(campo not in venda for campo in ("id", "data_venda", "itens", "total")):
                raise ValueError("Uma venda não contém todos os campos obrigatórios.")
            identificador = venda["id"]
            if type(identificador) is not int or identificador <= 0:
                raise ValueError("O ID da venda deve ser um inteiro positivo.")
            if identificador in ids_encontrados:
                raise ValueError("Há IDs de venda duplicados no arquivo.")
            ids_encontrados.add(identificador)

            data_venda = venda["data_venda"]
            if not isinstance(data_venda, str):
                raise ValueError("A data da venda deve estar no formato AAAA-MM-DD.")
            try:
                if date.fromisoformat(data_venda).isoformat() != data_venda:
                    raise ValueError
            except ValueError as erro:
                raise ValueError("A data da venda deve ser uma data ISO válida.") from erro

            itens = venda["itens"]
            if not isinstance(itens, list) or not itens:
                raise ValueError("A venda deve conter uma lista não vazia de itens.")

            total_itens = Decimal("0.00")
            for item in itens:
                if not isinstance(item, dict):
                    raise ValueError("Há um item de venda inválido no arquivo.")
                if any(
                    campo not in item
                    for campo in ("livro_id", "titulo", "quantidade", "preco_unitario")
                ):
                    raise ValueError("Um item não contém todos os campos obrigatórios.")
                if type(item["livro_id"]) is not int or item["livro_id"] <= 0:
                    raise ValueError("O ID do livro vendido deve ser um inteiro positivo.")
                if not isinstance(item["titulo"], str):
                    raise ValueError("O título do item vendido deve ser texto.")
                if type(item["quantidade"]) is not int or item["quantidade"] <= 0:
                    raise ValueError("A quantidade vendida deve ser um inteiro positivo.")
                if not _decimal_valido(item["preco_unitario"]):
                    raise ValueError("O preço unitário deve ser finito e não negativo.")
                preco = _valor_monetario(item["preco_unitario"])
                total_itens += preco * item["quantidade"]

            if not _decimal_valido(venda["total"]):
                raise ValueError("O total da venda deve ser finito e não negativo.")
            total_registrado = _valor_monetario(venda["total"])
            if total_registrado != total_itens.quantize(_CENTAVO):
                raise ValueError("O total da venda não corresponde à soma dos itens.")

        return vendas
    except (OSError, ValueError) as erro:
        print(f"Não foi possível carregar as vendas: {erro}")
        return None


def _salvar_vendas(vendas):
    """Salva o histórico de vendas e indica se a operação foi concluída."""
    try:
        salvar_dados(NOME_ARQUIVO, vendas)
        return True
    except (OSError, ValueError) as erro:
        print(f"Não foi possível salvar as vendas: {erro}")
        return False


def _buscar_livro(livros, identificador):
    for livro in livros:
        if livro["id"] == identificador:
            return livro
    return None


def _solicitar_quantidade():
    while True:
        valor = input("Quantidade a vender: ").strip()
        try:
            quantidade = int(valor)
            if quantidade > 0:
                return quantidade
        except ValueError:
            pass
        print("Informe uma quantidade inteira positiva.")


def _exibir_resumo_itens(itens, total):
    print("\nItens selecionados:")
    for item in itens:
        subtotal = _valor_monetario(item["preco_unitario"]) * item["quantidade"]
        print(
            f"ID {item['livro_id']} - {item['titulo']}: "
            f"{item['quantidade']} x R$ {_valor_monetario(item['preco_unitario']):.2f} "
            f"= R$ {subtotal:.2f}"
        )
    print(f"Total parcial: R$ {total:.2f}")


def _salvar_alteracoes_relacionadas(livros, vendas, livros_anteriores):
    """Salva estoque e vendas; restaura o estoque caso o histórico falhe."""
    if not salvar_livros(livros):
        print("A venda não foi registrada porque não foi possível salvar os livros.")
        return False

    if _salvar_vendas(vendas):
        return True

    if salvar_livros(deepcopy(livros_anteriores)):
        print("A venda não foi registrada e o estoque anterior foi restaurado.")
    else:
        print(
            "ERRO: não foi possível restaurar o estoque. "
            "Os arquivos livros.json e vendas.json precisam ser verificados."
        )
    return False


def registrar_venda():
    """Registra uma venda com um ou mais livros e atualiza o estoque."""
    livros = carregar_livros()
    if livros is None:
        print("Venda cancelada porque não foi possível carregar os livros.")
        return
    vendas = _carregar_vendas()
    if vendas is None:
        print("Venda cancelada porque não foi possível carregar o histórico.")
        return
    if not livros:
        print("Não há livros cadastrados para vender.")
        return

    print("\n=== Livros disponíveis ===")
    for livro in livros:
        print(
            f"ID: {livro['id']} | Título: {livro.get('titulo', '')} | "
            f"Preço: R$ {livro.get('preco', 'Não informado')} | "
            f"Quantidade disponível: {livro.get('quantidade', 0)}"
        )

    itens = []
    total = Decimal("0.00")
    while True:
        livro_id = solicitar_id("ID do livro: ")
        livro = _buscar_livro(livros, livro_id)
        if livro is None:
            print(f"Não existe livro cadastrado com o ID {livro_id}.")
            continue
        preco_cadastrado = livro.get("preco")
        if not _decimal_valido(preco_cadastrado):
            print("Este livro não pode ser vendido: o preço cadastrado é inválido.")
            continue

        quantidade = _solicitar_quantidade()
        item_existente = None
        for item in itens:
            if item["livro_id"] == livro_id:
                item_existente = item
                break
        quantidade_anterior = item_existente["quantidade"] if item_existente else 0
        quantidade_nova = quantidade_anterior + quantidade
        estoque = livro.get("quantidade")
        if type(estoque) is not int or estoque < 0:
            print("Este livro não pode ser vendido: o estoque cadastrado é inválido.")
            continue
        if quantidade_nova > estoque:
            print(
                f"Estoque insuficiente. Disponível para esta venda: "
                f"{estoque - quantidade_anterior}."
            )
            continue

        preco_unitario = _valor_monetario(preco_cadastrado)
        if item_existente is None:
            itens.append(
                {
                    "livro_id": livro_id,
                    "titulo": livro["titulo"],
                    "quantidade": quantidade,
                    "preco_unitario": float(preco_unitario),
                }
            )
        else:
            item_existente["quantidade"] += quantidade
        total += preco_unitario * quantidade
        total = total.quantize(_CENTAVO)
        _exibir_resumo_itens(itens, total)

        while True:
            continuar = input("Adicionar outro livro? (s/n): ").strip().lower()
            if continuar in ("s", "sim"):
                break
            if continuar in ("n", "nao", "não"):
                break
            print("Resposta inválida. Digite s para continuar ou n para finalizar.")
        if continuar in ("n", "nao", "não"):
            break

    venda = {
        "id": max((item["id"] for item in vendas), default=0) + 1,
        "data_venda": date.today().isoformat(),
        "itens": itens,
        "total": float(total.quantize(_CENTAVO)),
    }

    print("\n=== Resumo da venda ===")
    print(f"ID da venda: {venda['id']}")
    print(f"Data: {venda['data_venda']}")
    _exibir_resumo_itens(itens, total)
    while True:
        confirmacao = input("Confirma a venda? (s/n): ").strip().lower()
        if confirmacao in ("s", "sim"):
            break
        if confirmacao in ("n", "nao", "não"):
            print("Venda cancelada. Nenhum dado foi alterado.")
            return
        print("Resposta inválida. Digite s para confirmar ou n para cancelar.")

    livros_anteriores = deepcopy(livros)
    for item in itens:
        livro = _buscar_livro(livros, item["livro_id"])
        livro["quantidade"] -= item["quantidade"]
    vendas.append(venda)

    if _salvar_alteracoes_relacionadas(livros, vendas, livros_anteriores):
        print(f"Venda registrada com sucesso. Total: R$ {total:.2f}")


def listar_historico_vendas():
    """Exibe o histórico das vendas usando os dados registrados na operação."""
    vendas = _carregar_vendas()
    if vendas is None:
        return
    if not vendas:
        print("O histórico de vendas está vazio.")
        return

    print("\n=== Histórico de vendas ===")
    for venda in vendas:
        print(f"ID da venda: {venda['id']}")
        print(f"Data da venda: {venda['data_venda']}")
        for item in venda["itens"]:
            preco = _valor_monetario(item["preco_unitario"])
            subtotal = preco * item["quantidade"]
            print(f"  ID do livro: {item['livro_id']}")
            print(f"  Título: {item['titulo']}")
            print(f"  Quantidade: {item['quantidade']}")
            print(f"  Preço unitário: R$ {preco:.2f}")
            print(f"  Subtotal: R$ {subtotal:.2f}")
        print(f"Total: R$ {_valor_monetario(venda['total']):.2f}")
        print("-" * 40)


def menu_gerenciamento_vendas():
    """Mantém aberto o menu de vendas até que o funcionário escolha voltar."""
    while True:
        print("\n===== GERENCIAMENTO DE VENDAS =====")
        print("1. Registrar venda")
        print("2. Listar histórico de vendas")
        print("3. Voltar")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            registrar_venda()
        elif opcao == "2":
            listar_historico_vendas()
        elif opcao == "3":
            break
        else:
            print("Opção inválida. Escolha um número de 1 a 3.")
