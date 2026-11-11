from persistencia import carregar_dados, salvar_dados


NOME_ARQUIVO = "usuarios.json"
_SEM_VALOR = object()


def _normalizar_cpf(cpf):
    """Remove a pontuação permitida e os espaços de um CPF digitado."""
    if not isinstance(cpf, str):
        return None

    caracteres = []
    for caractere in cpf:
        if caractere in ".-" or caractere.isspace():
            continue
        if not caractere.isascii() or not caractere.isdigit():
            return None
        caracteres.append(caractere)
    return "".join(caracteres)


def validar_cpf(cpf):
    """Valida matematicamente um CPF com ou sem pontuação."""
    cpf_limpo = _normalizar_cpf(cpf)
    if cpf_limpo is None or len(cpf_limpo) != 11:
        return False
    if len(set(cpf_limpo)) == 1:
        return False

    digitos = [int(digito) for digito in cpf_limpo]

    soma_primeiro_digito = 0
    for indice in range(9):
        soma_primeiro_digito += digitos[indice] * (10 - indice)
    resto = soma_primeiro_digito % 11
    primeiro_digito = 0 if resto < 2 else 11 - resto
    if digitos[9] != primeiro_digito:
        return False

    soma_segundo_digito = 0
    for indice in range(10):
        soma_segundo_digito += digitos[indice] * (11 - indice)
    resto = soma_segundo_digito % 11
    segundo_digito = 0 if resto < 2 else 11 - resto
    return digitos[10] == segundo_digito


def _carregar_usuarios():
    """Carrega os usuários e verifica a estrutura básica dos registros."""
    try:
        usuarios = carregar_dados(NOME_ARQUIVO)
        if not isinstance(usuarios, list):
            raise ValueError("O arquivo de usuários deve conter uma lista.")

        for usuario in usuarios:
            if (
                not isinstance(usuario, dict)
                or type(usuario.get("id")) is not int
                or not isinstance(usuario.get("cpf"), str)
                or not isinstance(usuario.get("nome"), str)
            ):
                raise ValueError("Há um registro de usuário inválido no arquivo.")

        return usuarios
    except (OSError, ValueError) as erro:
        print(f"Não foi possível carregar os usuários: {erro}")
        return None


def _salvar_usuarios(usuarios):
    """Salva a lista de usuários e informa se a operação foi concluída."""
    try:
        salvar_dados(NOME_ARQUIVO, usuarios)
        return True
    except (OSError, ValueError) as erro:
        print(f"Não foi possível salvar os usuários: {erro}")
        return False


def _solicitar_texto(mensagem, obrigatorio=False, valor_atual=_SEM_VALOR):
    while True:
        valor = input(mensagem).strip()

        if valor == "":
            if valor_atual is not _SEM_VALOR and valor_atual != "":
                return valor_atual
            if obrigatorio:
                print("Este campo é obrigatório. Informe um valor.")
                continue
        return valor


def _solicitar_cpf(mensagem, permitir_vazio=False, cpf_atual=_SEM_VALOR):
    while True:
        valor = input(mensagem).strip()

        if not valor and permitir_vazio:
            return cpf_atual

        cpf_limpo = _normalizar_cpf(valor)
        if validar_cpf(valor):
            return cpf_limpo

        print("CPF inválido. Informe um CPF válido com 11 dígitos.")


def _solicitar_id():
    while True:
        valor = input("ID do usuário: ").strip()
        try:
            identificador = int(valor)
            if identificador > 0:
                return identificador
        except ValueError:
            pass

        print("Informe um ID numérico positivo.")


def _encontrar_usuario_por_cpf(usuarios, cpf):
    for usuario in usuarios:
        if usuario["cpf"] == cpf:
            return usuario
    return None


def _encontrar_usuario_por_id(usuarios, identificador):
    for usuario in usuarios:
        if usuario["id"] == identificador:
            return usuario
    return None


def _exibir_usuario(usuario):
    print(f"ID: {usuario['id']}")
    print(f"CPF: {usuario['cpf']}")
    print(f"Nome: {usuario.get('nome', '')}")
    print(f"Telefone: {usuario.get('telefone') or 'Não informado'}")
    print(f"E-mail: {usuario.get('email') or 'Não informado'}")


def cadastrar_usuario():
    """Solicita os dados e cadastra um novo usuário."""
    usuarios = _carregar_usuarios()
    if usuarios is None:
        return

    print("\n=== Cadastro de usuário ===")
    cpf = _solicitar_cpf("CPF: ")
    if _encontrar_usuario_por_cpf(usuarios, cpf) is not None:
        print("Já existe um usuário cadastrado com esse CPF.")
        return

    nome = _solicitar_texto("Nome completo: ", obrigatorio=True)
    telefone = _solicitar_texto("Telefone (opcional): ")
    email = _solicitar_texto("E-mail (opcional): ")

    maior_id = max((usuario["id"] for usuario in usuarios), default=0)
    novo_usuario = {
        "id": maior_id + 1,
        "cpf": cpf,
        "nome": nome,
        "telefone": telefone,
        "email": email,
    }
    usuarios.append(novo_usuario)

    if _salvar_usuarios(usuarios):
        print(f"Usuário cadastrado com sucesso. ID: {novo_usuario['id']}")


def listar_usuarios():
    """Exibe os dados de todos os usuários cadastrados."""
    usuarios = _carregar_usuarios()
    if usuarios is None:
        return
    if not usuarios:
        print("Não há usuários cadastrados.")
        return

    print("\n=== Usuários cadastrados ===")
    for usuario in usuarios:
        _exibir_usuario(usuario)
        print("-" * 32)


def consultar_usuario():
    """Localiza e exibe um usuário pelo CPF."""
    usuarios = _carregar_usuarios()
    if usuarios is None:
        return
    if not usuarios:
        print("Não há usuários cadastrados.")
        return

    cpf = _solicitar_cpf("CPF do usuário: ")
    usuario = _encontrar_usuario_por_cpf(usuarios, cpf)
    if usuario is None:
        print("Nenhum usuário foi encontrado com esse CPF.")
        return

    print("\n=== Usuário encontrado ===")
    _exibir_usuario(usuario)


def alterar_usuario():
    """Altera os dados de um usuário, preservando campos deixados em branco."""
    usuarios = _carregar_usuarios()
    if usuarios is None:
        return
    if not usuarios:
        print("Não há usuários cadastrados para alterar.")
        return

    cpf_busca = _solicitar_cpf("CPF do usuário que será alterado: ")
    usuario = _encontrar_usuario_por_cpf(usuarios, cpf_busca)
    if usuario is None:
        print("Nenhum usuário foi encontrado com esse CPF.")
        return

    print("Deixe um campo em branco para manter o valor atual.")
    cpf_digitado = _solicitar_cpf(
        f"Novo CPF [{usuario['cpf']}]: ",
        permitir_vazio=True,
        cpf_atual=usuario["cpf"],
    )
    outro_usuario = _encontrar_usuario_por_cpf(usuarios, cpf_digitado)
    if outro_usuario is not None and outro_usuario["id"] != usuario["id"]:
        print("Não foi possível alterar: esse CPF pertence a outro usuário.")
        return

    usuario_atualizado = usuario.copy()
    usuario_atualizado["cpf"] = cpf_digitado
    usuario_atualizado["nome"] = _solicitar_texto(
        f"Nome completo [{usuario.get('nome', '')}]: ",
        obrigatorio=True,
        valor_atual=usuario.get("nome", ""),
    )
    usuario_atualizado["telefone"] = _solicitar_texto(
        f"Telefone [{usuario.get('telefone', '')}]: ",
        valor_atual=usuario.get("telefone", ""),
    )
    usuario_atualizado["email"] = _solicitar_texto(
        f"E-mail [{usuario.get('email', '')}]: ",
        valor_atual=usuario.get("email", ""),
    )

    indice = usuarios.index(usuario)
    usuarios[indice] = usuario_atualizado
    if _salvar_usuarios(usuarios):
        print("Usuário alterado com sucesso.")


def excluir_usuario():
    """Solicita confirmação e exclui um usuário pelo ID interno."""
    usuarios = _carregar_usuarios()
    if usuarios is None:
        return
    if not usuarios:
        print("Não há usuários cadastrados para excluir.")
        return

    identificador = _solicitar_id()
    usuario = _encontrar_usuario_por_id(usuarios, identificador)
    if usuario is None:
        print(f"Nenhum usuário foi encontrado com o ID {identificador}.")
        return

    print("Usuário selecionado para exclusão:")
    print(f"ID: {usuario['id']}")
    print(f"Nome: {usuario.get('nome', '')}")
    print(f"CPF: {usuario['cpf']}")

    while True:
        confirmacao = input("Confirma a exclusão? (s/n): ").strip().lower()
        if confirmacao in ("s", "sim"):
            usuarios.remove(usuario)
            if _salvar_usuarios(usuarios):
                print("Usuário excluído com sucesso.")
            return
        if confirmacao in ("n", "nao", "não"):
            print("Exclusão cancelada. Nenhum dado foi alterado.")
            return
        print("Resposta inválida. Digite s para confirmar ou n para cancelar.")


def menu_gerenciamento_usuarios():
    """Mantém aberto o menu de usuários até que o funcionário volte."""
    while True:
        print("\n=== Gerenciamento de usuários ===")
        print("1. Cadastrar usuário")
        print("2. Listar usuários")
        print("3. Consultar usuário pelo CPF")
        print("4. Alterar usuário")
        print("5. Excluir usuário pelo ID")
        print("6. Voltar")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            cadastrar_usuario()
        elif opcao == "2":
            listar_usuarios()
        elif opcao == "3":
            consultar_usuario()
        elif opcao == "4":
            alterar_usuario()
        elif opcao == "5":
            excluir_usuario()
        elif opcao == "6":
            break
        else:
            print("Opção inválida. Escolha um número de 1 a 6.")