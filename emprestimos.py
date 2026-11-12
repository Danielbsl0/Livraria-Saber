from copy import deepcopy
from datetime import date, datetime

from entradas import solicitar_id
from livros import carregar_livros, salvar_livros
from persistencia import carregar_dados, salvar_dados
from usuarios import carregar_usuarios


NOME_ARQUIVO = "emprestimos.json"
_STATUS_EMPRESTADO = "emprestado"
_STATUS_DEVOLVIDO = "devolvido"


def _data_iso_valida(valor, permitir_none=False):
    if permitir_none and valor is None:
        return True
    if not isinstance(valor, str):
        return False
    try:
        return date.fromisoformat(valor).isoformat() == valor
    except ValueError:
        return False


def _carregar_emprestimos():
    """Carrega e valida os registros de empréstimo do arquivo JSON."""
    try:
        emprestimos = carregar_dados(NOME_ARQUIVO)
        if not isinstance(emprestimos, list):
            raise ValueError("O arquivo de empréstimos deve conter uma lista.")

        campos = (
            "id",
            "usuario_id",
            "livro_id",
            "data_emprestimo",
            "data_prevista_devolucao",
            "data_devolucao",
            "status",
        )
        ids_encontrados = set()
        for emprestimo in emprestimos:
            if not isinstance(emprestimo, dict):
                raise ValueError("Há um registro de empréstimo inválido no arquivo.")
            if any(campo not in emprestimo for campo in campos):
                raise ValueError("Um empréstimo não contém todos os campos obrigatórios.")
            if any(
                type(emprestimo.get(campo)) is not int or emprestimo[campo] <= 0
                for campo in ("id", "usuario_id", "livro_id")
            ):
                raise ValueError("Os IDs do empréstimo devem ser inteiros positivos.")
            if emprestimo["id"] in ids_encontrados:
                raise ValueError("Há IDs de empréstimo duplicados no arquivo.")
            ids_encontrados.add(emprestimo["id"])
            if not _data_iso_valida(emprestimo.get("data_emprestimo")):
                raise ValueError("A data de empréstimo deve estar no formato AAAA-MM-DD.")
            if not _data_iso_valida(emprestimo.get("data_prevista_devolucao")):
                raise ValueError(
                    "A data prevista deve estar no formato AAAA-MM-DD."
                )
            if not _data_iso_valida(emprestimo.get("data_devolucao"), permitir_none=True):
                raise ValueError("A data de devolução deve ser uma data ISO ou nula.")
            data_emprestimo = date.fromisoformat(emprestimo["data_emprestimo"])
            data_prevista = date.fromisoformat(
                emprestimo["data_prevista_devolucao"]
            )
            if data_prevista < data_emprestimo:
                raise ValueError(
                    "A data prevista de devolução não pode ser anterior à data do empréstimo."
                )
            if emprestimo["data_devolucao"] is not None:
                data_devolucao = date.fromisoformat(emprestimo["data_devolucao"])
                if data_devolucao < data_emprestimo:
                    raise ValueError(
                        "A data de devolução não pode ser anterior à data do empréstimo."
                    )
            if emprestimo.get("status") not in (
                _STATUS_EMPRESTADO,
                _STATUS_DEVOLVIDO,
            ):
                raise ValueError("O status do empréstimo é inválido.")
            if (
                emprestimo["status"] == _STATUS_EMPRESTADO
                and emprestimo["data_devolucao"] is not None
            ) or (
                emprestimo["status"] == _STATUS_DEVOLVIDO
                and emprestimo["data_devolucao"] is None
            ):
                raise ValueError("O status e a data de devolução são inconsistentes.")

        return emprestimos
    except (OSError, ValueError) as erro:
        print(f"Não foi possível carregar os empréstimos: {erro}")
        return None


def _salvar_emprestimos(emprestimos):
    """Salva os empréstimos e informa se a gravação foi concluída."""
    try:
        salvar_dados(NOME_ARQUIVO, emprestimos)
        return True
    except (OSError, ValueError) as erro:
        print(f"Não foi possível salvar os empréstimos: {erro}")
        return False


def _salvar_alteracoes_relacionadas(livros, emprestimos, livros_anteriores):
    """Grava livros e empréstimos juntos, restaurando dados em caso de falha."""
    if not salvar_livros(livros):
        print("Empréstimos não foram alterados porque não foi possível salvar os livros.")
        return False

    if _salvar_emprestimos(emprestimos):
        return True

    if salvar_livros(deepcopy(livros_anteriores)):
        print("As alterações foram desfeitas; nenhum empréstimo foi registrado.")
    else:
        print(
            "ERRO: não foi possível restaurar os livros. "
            "Os arquivos precisam ser verificados, pois podem estar inconsistentes."
        )
    return False


def _encontrar_por_id(registros, identificador):
    for registro in registros:
        if registro["id"] == identificador:
            return registro
    return None


def _solicitar_data_prevista(data_emprestimo):
    while True:
        valor = input("Data prevista de devolução (DD/MM/AAAA): ").strip()
        try:
            data_prevista = datetime.strptime(valor, "%d/%m/%Y").date()
        except ValueError:
            print("Data inválida. Informe uma data existente no formato DD/MM/AAAA.")
            continue

        if data_prevista.strftime("%d/%m/%Y") != valor:
            print("Data inválida. Informe uma data existente no formato DD/MM/AAAA.")
            continue

        if data_prevista < data_emprestimo:
            print("A data prevista não pode ser anterior à data do empréstimo.")
            continue
        return data_prevista


def _exibir_dados_emprestimo(emprestimo, usuarios, livros):
    usuario = _encontrar_por_id(usuarios, emprestimo["usuario_id"])
    livro = _encontrar_por_id(livros, emprestimo["livro_id"])

    print(f"ID do empréstimo: {emprestimo['id']}")
    if usuario is None:
        print(f"Usuário: Não encontrado (ID {emprestimo['usuario_id']})")
    else:
        print(f"Usuário: {usuario.get('nome', 'Nome não informado')}")
    if livro is None:
        print(f"Livro: Não encontrado (ID {emprestimo['livro_id']})")
    else:
        print(f"Livro: {livro.get('titulo', 'Título não informado')}")
    print(f"Data do empréstimo: {emprestimo['data_emprestimo']}")
    print(f"Data prevista de devolução: {emprestimo['data_prevista_devolucao']}")
    data_devolucao = emprestimo.get("data_devolucao")
    print(f"Data de devolução: {data_devolucao or 'Ainda não devolvido'}")
    print(f"Status: {emprestimo['status']}")


def registrar_emprestimo():
    """Registra empréstimo, reduzindo o estoque do livro com segurança."""
    usuarios = carregar_usuarios()
    livros = carregar_livros()
    emprestimos = _carregar_emprestimos()
    if usuarios is None or livros is None or emprestimos is None:
        print("Empréstimo não registrado porque não foi possível carregar todos os dados.")
        return

    usuario_id = solicitar_id("ID do usuário: ")
    usuario = _encontrar_por_id(usuarios, usuario_id)
    if usuario is None:
        print(f"Não existe usuário cadastrado com o ID {usuario_id}.")
        return

    livro_id = solicitar_id("ID do livro: ")
    livro = _encontrar_por_id(livros, livro_id)
    if livro is None:
        print(f"Não existe livro cadastrado com o ID {livro_id}.")
        return

    quantidade = livro.get("quantidade")
    if type(quantidade) is not int or quantidade < 0:
        print("Não foi possível registrar: a quantidade do livro está inválida.")
        return
    if quantidade == 0:
        print("Não há exemplares disponíveis desse livro para empréstimo.")
        return

    data_emprestimo = date.today()
    data_prevista = _solicitar_data_prevista(data_emprestimo)
    maior_id = max((item["id"] for item in emprestimos), default=0)
    novo_emprestimo = {
        "id": maior_id + 1,
        "usuario_id": usuario_id,
        "livro_id": livro_id,
        "data_emprestimo": data_emprestimo.isoformat(),
        "data_prevista_devolucao": data_prevista.isoformat(),
        "data_devolucao": None,
        "status": _STATUS_EMPRESTADO,
    }

    livros_anteriores = deepcopy(livros)
    livro["quantidade"] -= 1
    emprestimos.append(novo_emprestimo)

    if _salvar_alteracoes_relacionadas(livros, emprestimos, livros_anteriores):
        print(f"Empréstimo registrado com sucesso. ID: {novo_emprestimo['id']}")


def _listar_emprestimos(filtrar_abertos=False):
    emprestimos = _carregar_emprestimos()
    if emprestimos is None:
        return
    if filtrar_abertos:
        emprestimos = [
            item for item in emprestimos if item["status"] == _STATUS_EMPRESTADO
        ]
    if not emprestimos:
        if filtrar_abertos:
            print("Não há empréstimos em aberto.")
        else:
            print("Não há empréstimos cadastrados.")
        return

    usuarios = carregar_usuarios()
    livros = carregar_livros()
    if usuarios is None or livros is None:
        print("Não foi possível exibir os empréstimos sem carregar usuários e livros.")
        return

    titulo = "Empréstimos em aberto" if filtrar_abertos else "Todos os empréstimos"
    print(f"\n=== {titulo} ===")
    for emprestimo in emprestimos:
        _exibir_dados_emprestimo(emprestimo, usuarios, livros)
        print("-" * 40)


def listar_emprestimos():
    """Exibe o histórico completo dos empréstimos."""
    _listar_emprestimos()


def listar_emprestimos_em_aberto():
    """Exibe somente os empréstimos ainda não devolvidos."""
    _listar_emprestimos(filtrar_abertos=True)


def registrar_devolucao():
    """Registra a devolução e devolve o exemplar ao estoque."""
    emprestimos = _carregar_emprestimos()
    livros = carregar_livros()
    usuarios = carregar_usuarios()
    if emprestimos is None or livros is None or usuarios is None:
        print("Devolução não registrada porque não foi possível carregar todos os dados.")
        return

    identificador = solicitar_id("ID do empréstimo: ")
    emprestimo = _encontrar_por_id(emprestimos, identificador)
    if emprestimo is None:
        print(f"Não existe empréstimo cadastrado com o ID {identificador}.")
        return
    if emprestimo["status"] != _STATUS_EMPRESTADO:
        print("Este empréstimo já foi devolvido; não é possível devolvê-lo novamente.")
        return

    livro = _encontrar_por_id(livros, emprestimo["livro_id"])
    _exibir_dados_emprestimo(emprestimo, usuarios, livros)
    if livro is None:
        print("A devolução não pode ser registrada: o livro relacionado não foi encontrado.")
        return
    quantidade = livro.get("quantidade")
    if type(quantidade) is not int or quantidade < 0:
        print("A devolução não pode ser registrada: a quantidade do livro está inválida.")
        return

    while True:
        confirmacao = input("Confirma a devolução? (s/n): ").strip().lower()
        if confirmacao in ("s", "sim"):
            break
        if confirmacao in ("n", "nao", "não"):
            print("Devolução cancelada. Nenhum dado foi alterado.")
            return
        print("Resposta inválida. Digite s para confirmar ou n para cancelar.")

    livros_anteriores = deepcopy(livros)
    emprestimo["status"] = _STATUS_DEVOLVIDO
    emprestimo["data_devolucao"] = date.today().isoformat()
    livro["quantidade"] += 1

    if _salvar_alteracoes_relacionadas(livros, emprestimos, livros_anteriores):
        print("Devolução registrada com sucesso.")


def possui_emprestimo_em_aberto(campo_relacionamento, identificador):
    """Informa se há empréstimo aberto ligado a um livro ou usuário."""
    if campo_relacionamento not in ("livro_id", "usuario_id"):
        print("Tipo de relacionamento de empréstimo inválido.")
        return None

    emprestimos = _carregar_emprestimos()
    if emprestimos is None:
        return None
    for emprestimo in emprestimos:
        if (
            emprestimo[campo_relacionamento] == identificador
            and emprestimo["status"] == _STATUS_EMPRESTADO
        ):
            return True
    return False


def menu_gerenciamento_emprestimos():
    """Exibe o menu de empréstimos até que o funcionário escolha voltar."""
    while True:
        print("\n===== GERENCIAMENTO DE EMPRÉSTIMOS =====")
        print("1. Registrar empréstimo")
        print("2. Listar todos os empréstimos")
        print("3. Listar empréstimos em aberto")
        print("4. Registrar devolução")
        print("5. Voltar")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            registrar_emprestimo()
        elif opcao == "2":
            listar_emprestimos()
        elif opcao == "3":
            listar_emprestimos_em_aberto()
        elif opcao == "4":
            registrar_devolucao()
        elif opcao == "5":
            break
        else:
            print("Opção inválida. Escolha um número de 1 a 5.")
