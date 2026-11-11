import math

from persistencia import carregar_dados, salvar_dados


NOME_ARQUIVO = "livros.json"
_SEM_VALOR = object()


def _carregar_livros():
    """Carrega os livros e verifica a estrutura básica dos dados."""
    try:
        livros = carregar_dados(NOME_ARQUIVO)
        if not isinstance(livros, list):
            raise ValueError("O arquivo de livros deve conter uma lista.")

        for livro in livros:
            if not isinstance(livro, dict) or not isinstance(livro.get("id"), int):
                raise ValueError("Há um registro de livro inválido no arquivo.")

        return livros
    except (OSError, ValueError) as erro:
        print(f"Não foi possível carregar os livros: {erro}")
        return None


def _salvar_livros(livros):
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


def _solicitar_id():
    while True:
        valor = input("ID do livro: ").strip()
        try:
            identificador = int(valor)
            if identificador > 0:
                return identificador
        except ValueError:
            pass

        print("Informe um ID numérico positivo.")


def _encontrar_livro(livros, identificador):
    for livro in livros:
        if livro["id"] == identificador:
            return livro
    return None


def cadastrar_livro():
    """Solicita os dados e cadastra um novo livro."""
    livros = _carregar_livros()
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

    if _salvar_livros(livros):
        print(f"Livro cadastrado com sucesso. ID: {novo_livro['id']}")


def listar_livros():
    """Exibe os dados de todos os livros cadastrados."""
    livros = _carregar_livros()
    if livros is None:
        return
    if not livros:
        print("Não há livros cadastrados.")
        return

    print("\n=== Livros cadastrados ===")
    for livro in livros:
        print(f"ID: {livro['id']}")
        print(f"Título: {livro.get('titulo', '')}")
        print(f"Autor: {livro.get('autor', '')}")
        print(f"Editora: {livro.get('editora') or 'Não informada'}")
        print(f"Gênero: {livro.get('genero') or 'Não informado'}")
        print(f"Ano de publicação: {livro.get('ano_publicacao') or 'Não informado'}")
        print(f"ISBN: {livro.get('isbn') or 'Não informado'}")
        print(f"Preço: R$ {livro.get('preco', 0):.2f}")
        print(f"Quantidade disponível: {livro.get('quantidade', 0)}")
        print("-" * 32)


def alterar_livro():
    """Altera os campos de um livro, mantendo os valores dos campos em branco."""
    livros = _carregar_livros()
    if livros is None:
        return
    if not livros:
        print("Não há livros cadastrados para alterar.")
        return

    identificador = _solicitar_id()
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
    if _salvar_livros(livros):
        print("Livro alterado com sucesso.")


def excluir_livro():
    """Solicita confirmação e exclui um livro existente."""
    livros = _carregar_livros()
    if livros is None:
        return
    if not livros:
        print("Não há livros cadastrados para excluir.")
        return

    identificador = _solicitar_id()
    livro = _encontrar_livro(livros, identificador)
    if livro is None:
        print(f"Não existe livro cadastrado com o ID {identificador}.")
        return

    while True:
        confirmacao = input(
            f"Confirma a exclusão de '{livro.get('titulo', '')}'? (s/n): "
        ).strip().lower()
        if confirmacao in ("s", "sim"):
            livros.remove(livro)
            if _salvar_livros(livros):
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
