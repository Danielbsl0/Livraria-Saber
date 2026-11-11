from persistencia import inicializar_arquivos
from livros import menu_gerenciamento_livros
from usuarios import menu_gerenciamento_usuarios


def exibir_menu_principal():
    print("\n=== Livraria Saber ===")
    print("1. Consultar catálogo de livros")
    print("2. Área do funcionário")
    print("3. Encerrar programa")


def consultar_catalogo():
    print("A consulta ao catálogo será implementada nas próximas etapas.")


def acessar_area_funcionario():
    while True:
        print("\n=== Área do funcionário ===")
        print("1. Gerenciar livros")
        print("2. Gerenciar usuários")
        print("3. Voltar ao menu principal")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            menu_gerenciamento_livros()
        elif opcao == "2":
            menu_gerenciamento_usuarios()
        elif opcao == "3":
            break
        else:
            print("Opção inválida. Escolha 1, 2 ou 3.")


def main():
    try:
        inicializar_arquivos()
    except OSError as erro:
        print(f"Não foi possível iniciar o programa: {erro}")
        return

    while True:
        exibir_menu_principal()
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            consultar_catalogo()
        elif opcao == "2":
            acessar_area_funcionario()
        elif opcao == "3":
            print("Programa encerrado.")
            break
        else:
            print("Opção inválida. Escolha 1, 2 ou 3.")


if __name__ == "__main__":
    main()
