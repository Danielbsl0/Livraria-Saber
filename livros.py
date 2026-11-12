import math

from entradas import solicitar_id
from persistencia import carregar_dados, salvar_dados


NOME_ARQUIVO = "livros.json"
_SEM_VALOR = object()


def carregar_livros(mensagem_erro="Não foi possível carregar os livros"):
    """Carrega os livros e verifica a estrutura básica dos dados."""
    try:
        livros = carregar_dados(NOME_ARQUIVO)
        if not isinstance(livros, list):
            raise ValueError("O arquivo de livros deve conter uma lista.")

        ids_encontrados = set()
        for livro in livros:
            if (
                not isinstance(livro, dict)
                or type(livro.get("id")) is not int
                or livro["id"] <= 0
                or not isinstance(livro.get("titulo"), str)
                or not livro["titulo"].strip()
                or not isinstance(livro.get("autor"), str)
                or not livro["autor"].strip()
            ):
                raise ValueError("Há um registro de livro inválido no arquivo.")
            if livro["id"] in ids_encontrados:
                raise ValueError("Há IDs de livro duplicados no arquivo.")
            ids_encontrados.add(livro["id"])

            preco = livro.get("preco")
            if (
                isinstance(preco, bool)
                or not isinstance(preco, (int, float))
                or (isinstance(preco, float) and not math.isfinite(preco))
                or preco < 0
            ):
                raise ValueError("O preço de cada livro deve ser finito e não negativo.")

            quantidade = livro.get("quantidade")
            if type(quantidade) is not int or quantidade < 0:
                raise ValueError("A quantidade de cada livro deve ser um inteiro não negativo.")

            for campo in ("editora", "genero", "isbn"):
                if campo in livro and not isinstance(livro[campo], str):
                    raise ValueError(f"O campo {campo} do livro deve ser texto.")

            ano = livro.get("ano_publicacao")
            if ano is not None and (type(ano) is not int or ano <= 0):
                raise ValueError("O ano de publicação deve ser um inteiro positivo ou nulo.")

        return livros
    except (OSError, ValueError) as erro:
        print(f"{mensagem_erro}: {erro}")
        return None


def exibir_livro(livro, mostrar_id=True):
    """Exibe os dados de um livro, com ID opcional para a área pública."""
    if mostrar_id:
        print(f"ID: {livro['id']}")

    print(f"Título: {livro.get('titulo', '')}")
    print(f"Autor: {livro.get('autor', '')}")
    print(f"Editora: {livro.get('editora') or 'Não informada'}")
    print(f"Gênero: {livro.get('genero') or 'Não informado'}")

    ano = livro.get("ano_publicacao")
    if mostrar_id:
        ano = ano or "Não informado"
    elif ano is None:
        ano = "Não informado"
    print(f"Ano de publicação: {ano}")
    print(f"ISBN: {livro.get('isbn') or 'Não informado'}")

    preco = livro.get("preco", 0) if mostrar_id else livro.get("preco")
    if not mostrar_id and (
        not isinstance(preco, (int, float)) or isinstance(preco, bool)
    ):
        print("Preço: Não informado")
    else:
        print(f"Preço: R$ {preco:.2f}")

    quantidade = livro.get("quantidade", 0) if mostrar_id else livro.get("quantidade")
    if mostrar_id or quantidade is not None:
        print(f"Quantidade disponível: {quantidade}")


def salvar_livros(livros):
    """Salva a lista de livros e informa se a operação foi concluída."""
    try:
        salvar_dados(NOME_ARQUIVO, livros)
        return True
    except (OSError, ValueError) as erro:
        print(f"Não foi possível salvar os livros: {erro}")
        return False


def _solicitar_texto(mensagem, obrigatorio=False, valor_atual=_SEM_VALOR):
    while True:
        valor = input(mensagem).strip()

        if valor == "" and valor_atual is not _SEM_VALOR:
            return valor_atual
        if valor or not obrigatorio:
            return valor

        print("Este campo é obrigatório. Informe um valor.")


def _solicitar_ano(valor_atual=_SEM_VALOR):
    while True:
        valor = input("Ano de publicação (opcional): ").strip()

        if not valor and valor_atual is not _SEM_VALOR:
            return valor_atual
        if not valor:
            return None

        try:
            ano = int(valor)
            if ano > 0:
                return ano
        except ValueError:
            pass

        print("Informe um ano inteiro positivo ou deixe o campo em branco.")


def _solicitar_preco(valor_atual=_SEM_VALOR):
    while True:
        valor = input("Preço: ").strip()

        if not valor and valor_atual is not _SEM_VALOR:
            return valor_atual

        try:
            preco = float(valor.replace(",", "."))
            if math.isfinite(preco) and preco >= 0:
                return preco
        except ValueError:
            pass

        print("Informe um preço numérico não negativo (por exemplo, 29,90).")


def _solicitar_quantidade(valor_atual=_SEM_VALOR):
    while True:
        valor = input("Quantidade disponível: ").strip()

        if not valor and valor_atual is not _SEM_VALOR:
            return valor_atual

        try:
            quantidade = int(valor)
            if quantidade >= 0:
                return quantidade
        except ValueError:
            pass

        print("Informe uma quantidade inteira não negativa.")


def _encontrar_livro(livros, identificador):
    for livro in livros:
        if livro["id"] == identificador:
            return livro
    return None


def cadastrar_livro():
    """Solicita os dados e cadastra um novo livro."""
    livros = carregar_livros()
    if livros is None:
        return

    print("\n=== Cadastro de livro ===")
    titulo = _solicitar_texto("Título: ", obrigatorio=True)
    autor = _solicitar_texto("Autor: ", obrigatorio=True)
    editora = _solicitar_texto("Editora (opcional): ")
    genero = _solicitar_texto("Gênero (opcional): ")
    ano_publicacao = _solicitar_ano()
    isbn = _solicitar_texto("ISBN (opcional): ")
    preco = _solicitar_preco()
    quantidade = _solicitar_quantidade()

    maior_id = max((livro["id"] for livro in livros), default=0)
    novo_livro = {
        "id": maior_id + 1,
        "titulo": titulo,
        "autor": autor,
        "editora": editora,
        "genero": genero,
        "ano_publicacao": ano_publicacao,
        "isbn": isbn,
        "preco": preco,
        "quantidade": quantidade,
    }
    livros.append(novo_livro)

    if salvar_livros(livros):
        print(f"Livro cadastrado com sucesso. ID: {novo_livro['id']}")


def listar_livros():
    """Exibe os dados de todos os livros cadastrados."""
    livros = carregar_livros()
    if livros is None:
        return
    if not livros:
        print("Não há livros cadastrados.")
        return

    print("\n=== Livros cadastrados ===")
    for livro in livros:
        exibir_livro(livro)
        print("-" * 32)


def alterar_livro():
    """Altera os campos de um livro, mantendo os valores dos campos em branco."""
    livros = carregar_livros()
    if livros is None:
        return
    if not livros:
        print("Não há livros cadastrados para alterar.")
        return

    identificador = solicitar_id("ID do livro: ")
    livro = _encontrar_livro(livros, identificador)
    if livro is None:
        print(f"Não existe livro cadastrado com o ID {identificador}.")
        return

    print("Deixe um campo em branco para manter o valor atual.")
    livro_atualizado = livro.copy()
    livro_atualizado["titulo"] = _solicitar_texto(
        f"Título [{livro.get('titulo', '')}]: ",
        obrigatorio=True,
        valor_atual=livro.get("titulo", ""),
    )
    livro_atualizado["autor"] = _solicitar_texto(
        f"Autor [{livro.get('autor', '')}]: ",
        obrigatorio=True,
        valor_atual=livro.get("autor", ""),
    )
    livro_atualizado["editora"] = _solicitar_texto(
        f"Editora [{livro.get('editora', '')}]: ", valor_atual=livro.get("editora", "")
    )
    livro_atualizado["genero"] = _solicitar_texto(
        f"Gênero [{livro.get('genero', '')}]: ", valor_atual=livro.get("genero", "")
    )

    ano_atual = livro.get("ano_publicacao")
    while True:
        ano_digitado = input(
            f"Ano de publicação [{ano_atual if ano_atual is not None else ''}]: "
        ).strip()
        if not ano_digitado:
            livro_atualizado["ano_publicacao"] = ano_atual
            break
        try:
            ano = int(ano_digitado)
            if ano > 0:
                livro_atualizado["ano_publicacao"] = ano
                break
        except ValueError:
            pass
        print("Informe um ano inteiro positivo ou deixe o campo em branco.")

    livro_atualizado["isbn"] = _solicitar_texto(
        f"ISBN [{livro.get('isbn', '')}]: ", valor_atual=livro.get("isbn", "")
    )
    livro_atualizado["preco"] = _solicitar_preco(livro.get("preco", 0))
    livro_atualizado["quantidade"] = _solicitar_quantidade(
        livro.get("quantidade", 0)
    )

    indice = livros.index(livro)
    livros[indice] = livro_atualizado
    if salvar_livros(livros):
        print("Livro alterado com sucesso.")


def excluir_livro():
    """Solicita confirmação e exclui um livro existente."""
    livros = carregar_livros()
    if livros is None:
        return
    if not livros:
        print("Não há livros cadastrados para excluir.")
        return

    identificador = solicitar_id("ID do livro: ")
    livro = _encontrar_livro(livros, identificador)
    if livro is None:
        print(f"Não existe livro cadastrado com o ID {identificador}.")
        return

    from emprestimos import possui_emprestimo_em_aberto

    emprestimo_aberto = possui_emprestimo_em_aberto("livro_id", identificador)
    if emprestimo_aberto is None:
        print("Livro não excluído porque não foi possível verificar os empréstimos.")
        return
    if emprestimo_aberto:
        print("Livro não pode ser excluído enquanto possuir empréstimo em aberto.")
        return

    while True:
        confirmacao = input(
            f"Confirma a exclusão de '{livro.get('titulo', '')}'? (s/n): "
        ).strip().lower()
        if confirmacao in ("s", "sim"):
            livros.remove(livro)
            if salvar_livros(livros):
                print("Livro excluído com sucesso.")
            return
        if confirmacao in ("n", "nao", "não"):
            print("Exclusão cancelada. Nenhum dado foi alterado.")
            return
        print("Resposta inválida. Digite s para confirmar ou n para cancelar.")


def menu_gerenciamento_livros():
    """Mantém aberto o menu de gerenciamento até a opção de voltar."""
    while True:
        print("\n=== Gerenciamento de livros ===")
        print("1. Cadastrar livro")
        print("2. Listar livros")
        print("3. Alterar livro")
        print("4. Excluir livro")
        print("5. Voltar")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            cadastrar_livro()
        elif opcao == "2":
            listar_livros()
        elif opcao == "3":
            alterar_livro()
        elif opcao == "4":
            excluir_livro()
        elif opcao == "5":
            break
        else:
            print("Opção inválida. Escolha um número de 1 a 5.")
