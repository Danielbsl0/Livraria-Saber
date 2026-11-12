from livros import carregar_livros, exibir_livro


def _exibir_livros(livros, titulo_secao):
    print(f"\n=== {titulo_secao} ===")
    for livro in livros:
        exibir_livro(livro, mostrar_id=False)
        print("-" * 40)


def listar_todos_os_livros():
    """Exibe todos os livros cadastrados sem alterar o arquivo JSON."""
    livros = carregar_livros("Não foi possível carregar o catálogo")
    if livros is None:
        return
    if not livros:
        print("O catálogo está vazio. Não há livros cadastrados.")
        return

    _exibir_livros(livros, "Catálogo de livros")


def _pesquisar_livros(campo, descricao):
    """Pesquisa livros por trecho de texto, sem diferenciar maiúsculas."""
    livros = carregar_livros("Não foi possível carregar o catálogo")
    if livros is None:
        return
    if not livros:
        print("O catálogo está vazio. Não há livros cadastrados.")
        return

    while True:
        termo = input(f"Informe o {descricao} ou parte dele: ").strip()
        if termo:
            break
        print("A pesquisa não pode ficar vazia. Informe um termo.")

    termo = termo.casefold()
    encontrados = []
    for livro in livros:
        valor = livro.get(campo, "")
        if isinstance(valor, str) and termo in valor.casefold():
            encontrados.append(livro)

    if not encontrados:
        print("Nenhum livro corresponde à pesquisa.")
        return

    _exibir_livros(encontrados, f"Resultados da pesquisa por {descricao}")


def pesquisar_por_titulo():
    """Pesquisa livros por título completo ou parcial."""
    _pesquisar_livros("titulo", "título")


def pesquisar_por_autor():
    """Pesquisa livros por nome completo ou parcial do autor."""
    _pesquisar_livros("autor", "autor")


def pesquisar_por_genero():
    """Pesquisa livros por gênero completo ou parcial."""
    _pesquisar_livros("genero", "gênero")


def menu_catalogo():
    """Mantém aberto o catálogo público até a opção de voltar."""
    while True:
        print("\n===== CATÁLOGO DE LIVROS =====")
        print("1. Listar todos os livros")
        print("2. Pesquisar por título")
        print("3. Pesquisar por autor")
        print("4. Pesquisar por gênero")
        print("5. Voltar ao menu principal")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            listar_todos_os_livros()
        elif opcao == "2":
            pesquisar_por_titulo()
        elif opcao == "3":
            pesquisar_por_autor()
        elif opcao == "4":
            pesquisar_por_genero()
        elif opcao == "5":
            break
        else:
            print("Opção inválida. Escolha um número de 1 a 5.")