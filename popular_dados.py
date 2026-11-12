"""Popula a Livraria Saber com registros fictícios para demonstração local."""

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import os
from pathlib import Path
import sys
import tempfile
import unicodedata

import emprestimos
import persistencia
import usuarios
import vendas
from livros import carregar_livros


_CENTAVO = Decimal("0.01")


def _cpf_ficticio(base):
    """Gera dígitos verificadores para uma sequência sintética de demonstração."""
    digitos = [int(digito) for digito in base]
    soma = sum(digito * (10 - indice) for indice, digito in enumerate(digitos))
    resto = soma % 11
    primeiro = 0 if resto < 2 else 11 - resto
    digitos.append(primeiro)

    soma = sum(digito * (11 - indice) for indice, digito in enumerate(digitos))
    resto = soma % 11
    segundo = 0 if resto < 2 else 11 - resto
    digitos.append(segundo)
    cpf = "".join(str(digito) for digito in digitos)
    if not usuarios.validar_cpf(cpf):
        raise ValueError("Não foi possível gerar um CPF sintético válido.")
    return cpf


def _normalizar_texto(valor):
    texto = unicodedata.normalize("NFKD", valor).casefold()
    sem_acentos = "".join(
        caractere for caractere in texto
        if not unicodedata.combining(caractere)
    )
    return " ".join(sem_acentos.split())


def _chave_livro(livro):
    return (_normalizar_texto(livro["titulo"]), _normalizar_texto(livro["autor"]))


def _chave_cpf(cpf):
    cpf_normalizado = usuarios._normalizar_cpf(cpf)
    if cpf_normalizado is None or not usuarios.validar_cpf(cpf_normalizado):
        raise ValueError("Há um CPF inválido nos dados de demonstração ou existentes.")
    return cpf_normalizado


def _livros_demo():
    return [
        {
            "titulo": "A Biblioteca das Estrelas",
            "autor": "Helena Duarte",
            "editora": "Editora Horizonte",
            "genero": "Ficção científica",
            "ano_publicacao": 2021,
            "isbn": "DEMO-LS-0001",
            "preco": 48.90,
            "quantidade": 8,
        },
        {
            "titulo": "Receitas de um Jardim Pequeno",
            "autor": "Caio Nascimento",
            "editora": "Pomar Editorial",
            "genero": "Culinária",
            "ano_publicacao": 2020,
            "isbn": "DEMO-LS-0002",
            "preco": 36.50,
            "quantidade": 6,
        },
        {
            "titulo": "O Mapa das Chuvas",
            "autor": "Lia Monteiro",
            "editora": "Editora Horizonte",
            "genero": "Romance",
            "ano_publicacao": 2023,
            "isbn": "DEMO-LS-0003",
            "preco": 42.00,
            "quantidade": 5,
        },
        {
            "titulo": "Pequeno Guia de Astronomia",
            "autor": "Rui Campos",
            "editora": "Norte Editorial",
            "genero": "Divulgação científica",
            "ano_publicacao": 2019,
            "isbn": "DEMO-LS-0004",
            "preco": 31.75,
            "quantidade": 7,
        },
    ]


def _usuarios_demo():
    return [
        {
            "cpf": _cpf_ficticio("000000001"),
            "nome": "Pessoa Demonstrativa Um",
            "telefone": "+55 (00) 00000-0001",
            "email": "pessoa1@example.invalid",
        },
        {
            "cpf": _cpf_ficticio("000000002"),
            "nome": "Pessoa Demonstrativa Dois",
            "telefone": "+55 (00) 00000-0002",
            "email": "pessoa2@example.invalid",
        },
        {
            "cpf": _cpf_ficticio("000000003"),
            "nome": "Pessoa Demonstrativa Três",
            "telefone": "+55 (00) 00000-0003",
            "email": "pessoa3@example.invalid",
        },
    ]


def _carregar_bases():
    persistencia.inicializar_arquivos()
    bases = {
        "livros": carregar_livros(),
        "usuarios": usuarios.carregar_usuarios(),
        "emprestimos": emprestimos._carregar_emprestimos(),
        "vendas": vendas._carregar_vendas(),
    }
    if any(registros is None for registros in bases.values()):
        raise ValueError("A população foi cancelada porque há dados inválidos ou ilegíveis.")
    return bases


def _chave_emprestimo(registro, usuarios_por_id, livros_por_id):
    usuario = usuarios_por_id.get(registro["usuario_id"])
    livro = livros_por_id.get(registro["livro_id"])
    if usuario is None or livro is None:
        raise ValueError("Empréstimo contém referência a usuário ou livro inexistente.")
    return (
        _chave_cpf(usuario["cpf"]),
        _chave_livro(livro),
        registro["data_emprestimo"],
        registro["data_prevista_devolucao"],
        registro["data_devolucao"],
        registro["status"],
    )


def _preco_em_centavos(valor):
    if isinstance(valor, bool) or not isinstance(valor, (int, float, Decimal)):
        raise ValueError("Preço de venda inválido nos dados de demonstração.")
    try:
        preco = Decimal(str(valor)).quantize(_CENTAVO, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as erro:
        raise ValueError("Preço de venda inválido nos dados de demonstração.") from erro
    if not preco.is_finite() or preco < 0:
        raise ValueError("Preço de venda inválido nos dados de demonstração.")
    return int(preco * 100)


def _chave_venda(registro, livros_por_id):
    itens = []
    for item in registro["itens"]:
        livro = livros_por_id.get(item["livro_id"])
        if livro is None:
            raise ValueError("Venda contém referência a livro inexistente.")
        itens.append(
            (
                _chave_livro(livro),
                item["quantidade"],
                _preco_em_centavos(item["preco_unitario"]),
            )
        )
    return registro["data_venda"], tuple(sorted(itens))


def _validar_relacionamentos(livros, usuarios_registros, emprestimos_registros, vendas_registros):
    livros_por_id = {livro["id"]: livro for livro in livros}
    usuarios_por_id = {usuario["id"]: usuario for usuario in usuarios_registros}

    for registro in emprestimos_registros:
        if registro["usuario_id"] not in usuarios_por_id:
            raise ValueError("Empréstimo aponta para usuário inexistente.")
        if registro["livro_id"] not in livros_por_id:
            raise ValueError("Empréstimo aponta para livro inexistente.")
        if not emprestimos._data_iso_valida(registro["data_emprestimo"]):
            raise ValueError("Empréstimo contém data inválida.")
        if not emprestimos._data_iso_valida(registro["data_prevista_devolucao"]):
            raise ValueError("Empréstimo contém data prevista inválida.")
        data_inicio = date.fromisoformat(registro["data_emprestimo"])
        data_prevista = date.fromisoformat(registro["data_prevista_devolucao"])
        if data_prevista < data_inicio:
            raise ValueError("Data prevista do empréstimo antecede a data inicial.")
        data_devolucao = registro["data_devolucao"]
        if not emprestimos._data_iso_valida(data_devolucao, permitir_none=True):
            raise ValueError("Empréstimo contém data de devolução inválida.")
        if registro["status"] not in ("emprestado", "devolvido"):
            raise ValueError("Empréstimo contém status inválido.")
        if (registro["status"] == "emprestado") != (data_devolucao is None):
            raise ValueError("Status e data de devolução do empréstimo são inconsistentes.")
        if data_devolucao is not None and date.fromisoformat(data_devolucao) < data_inicio:
            raise ValueError("Data de devolução antecede a data inicial do empréstimo.")

    for venda in vendas_registros:
        data_venda = venda.get("data_venda")
        try:
            if date.fromisoformat(data_venda).isoformat() != data_venda:
                raise ValueError
        except (TypeError, ValueError) as erro:
            raise ValueError("Venda contém data inválida.") from erro
        itens = venda.get("itens")
        if not isinstance(itens, list) or not itens:
            raise ValueError("Venda deve conter ao menos um item.")
        total_centavos = 0
        for item in itens:
            if item["livro_id"] not in livros_por_id:
                raise ValueError("Venda aponta para livro inexistente.")
            if type(item["quantidade"]) is not int or item["quantidade"] <= 0:
                raise ValueError("Venda contém quantidade inválida.")
            total_centavos += _preco_em_centavos(item["preco_unitario"]) * item["quantidade"]
        if _preco_em_centavos(venda.get("total")) != total_centavos:
            raise ValueError("Total da venda não corresponde à soma dos itens.")

    return livros_por_id, usuarios_por_id


def _salvar_transacionalmente(arquivos_alterados):
    """Grava as listas e restaura os bytes anteriores se qualquer gravação falhar."""
    nomes = persistencia.NOMES_ARQUIVOS
    caminhos = {nome: persistencia._obter_caminho(nome) for nome in nomes}
    originais = {nome: caminhos[nome].read_bytes() for nome in nomes}

    try:
        for nome in nomes:
            if nome in arquivos_alterados:
                persistencia.salvar_dados(nome, arquivos_alterados[nome])
    except Exception as erro:
        falhas_restauracao = []
        for nome, caminho in caminhos.items():
            temporario = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    dir=caminho.parent,
                    prefix=f".{caminho.name}.",
                    suffix=".restore.tmp",
                    delete=False,
                ) as arquivo:
                    temporario = Path(arquivo.name)
                    arquivo.write(originais[nome])
                    arquivo.flush()
                os.replace(temporario, caminho)
                temporario = None
            except OSError as erro_restauracao:
                falhas_restauracao.append(f"{nome}: {erro_restauracao}")
            finally:
                if temporario is not None:
                    try:
                        temporario.unlink(missing_ok=True)
                    except OSError:
                        pass

        if falhas_restauracao:
            raise RuntimeError(
                "Falha ao gravar e ao restaurar os arquivos: "
                + "; ".join(falhas_restauracao)
            ) from erro
        raise OSError("Falha na gravação; os arquivos anteriores foram restaurados.") from erro


def popular_dados():
    """Inclui os dados de demonstração sem substituir nem duplicar registros."""
    bases = _carregar_bases()
    livros = bases["livros"]
    usuarios_registros = bases["usuarios"]
    emprestimos_registros = bases["emprestimos"]
    vendas_registros = bases["vendas"]

    livros_por_chave = {_chave_livro(livro): livro for livro in livros}
    proximo_id_livro = max((livro["id"] for livro in livros), default=0) + 1
    novos_livros = []
    livros_demo_por_chave = {}
    ignorados = 0
    for modelo in _livros_demo():
        chave = _chave_livro(modelo)
        existente = livros_por_chave.get(chave)
        if existente is not None:
            livro = existente
            ignorados += 1
        else:
            livro = {"id": proximo_id_livro, **modelo}
            proximo_id_livro += 1
            livros.append(livro)
            livros_por_chave[chave] = livro
            novos_livros.append(livro)
        livros_demo_por_chave[chave] = livro

    usuarios_por_cpf = {_chave_cpf(usuario["cpf"]): usuario for usuario in usuarios_registros}
    proximo_id_usuario = max((usuario["id"] for usuario in usuarios_registros), default=0) + 1
    novos_usuarios = []
    usuarios_demo_por_cpf = {}
    for modelo in _usuarios_demo():
        chave = _chave_cpf(modelo["cpf"])
        existente = usuarios_por_cpf.get(chave)
        if existente is not None:
            usuario = existente
            ignorados += 1
        else:
            usuario = {"id": proximo_id_usuario, **modelo}
            proximo_id_usuario += 1
            usuarios_registros.append(usuario)
            usuarios_por_cpf[chave] = usuario
            novos_usuarios.append(usuario)
        usuarios_demo_por_cpf[chave] = usuario

    livros_por_id, usuarios_por_id = _validar_relacionamentos(
        livros, usuarios_registros, emprestimos_registros, vendas_registros
    )
    chaves_emprestimos = {
        _chave_emprestimo(registro, usuarios_por_id, livros_por_id)
        for registro in emprestimos_registros
    }
    proximo_id_emprestimo = max(
        (registro["id"] for registro in emprestimos_registros), default=0
    ) + 1
    novos_emprestimos = []
    dados_emprestimos_demo = [
        {
            "usuario_cpf": _cpf_ficticio("000000001"),
            "livro": ("A Biblioteca das Estrelas", "Helena Duarte"),
            "data_emprestimo": "2026-10-10",
            "data_prevista_devolucao": "2026-10-24",
            "data_devolucao": "2026-10-20",
            "status": "devolvido",
        },
        {
            "usuario_cpf": _cpf_ficticio("000000002"),
            "livro": ("O Mapa das Chuvas", "Lia Monteiro"),
            "data_emprestimo": "2026-11-05",
            "data_prevista_devolucao": "2026-11-19",
            "data_devolucao": None,
            "status": "emprestado",
        },
    ]
    for modelo in dados_emprestimos_demo:
        usuario = usuarios_demo_por_cpf[_chave_cpf(modelo["usuario_cpf"])]
        chave_livro = tuple(_normalizar_texto(valor) for valor in modelo["livro"])
        livro = livros_demo_por_chave[chave_livro]
        registro = {
            "usuario_id": usuario["id"],
            "livro_id": livro["id"],
            "data_emprestimo": modelo["data_emprestimo"],
            "data_prevista_devolucao": modelo["data_prevista_devolucao"],
            "data_devolucao": modelo["data_devolucao"],
            "status": modelo["status"],
        }
        chave = _chave_emprestimo(registro, usuarios_por_id, livros_por_id)
        if chave in chaves_emprestimos:
            ignorados += 1
            continue
        registro["id"] = proximo_id_emprestimo
        proximo_id_emprestimo += 1
        emprestimos_registros.append(registro)
        chaves_emprestimos.add(chave)
        novos_emprestimos.append(registro)

    chaves_vendas = {
        _chave_venda(registro, livros_por_id) for registro in vendas_registros
    }
    proximo_id_venda = max((registro["id"] for registro in vendas_registros), default=0) + 1
    novas_vendas = []
    modelos_vendas = [
        {
            "data_venda": "2026-11-06",
            "itens": [
                (("A Biblioteca das Estrelas", "Helena Duarte"), 1, 48.90),
                (("Receitas de um Jardim Pequeno", "Caio Nascimento"), 1, 36.50),
            ],
        },
        {
            "data_venda": "2026-11-09",
            "itens": [
                (("O Mapa das Chuvas", "Lia Monteiro"), 1, 42.00),
            ],
        },
    ]
    for modelo in modelos_vendas:
        itens = []
        total = Decimal("0.00")
        for livro_nome, quantidade, preco_unitario in modelo["itens"]:
            chave_livro = tuple(_normalizar_texto(valor) for valor in livro_nome)
            livro = livros_demo_por_chave[chave_livro]
            itens.append(
                {
                    "livro_id": livro["id"],
                    "titulo": livro["titulo"],
                    "quantidade": quantidade,
                    "preco_unitario": preco_unitario,
                }
            )
            total += Decimal(str(preco_unitario)).quantize(_CENTAVO) * quantidade
        registro = {
            "data_venda": modelo["data_venda"],
            "itens": itens,
            "total": float(total.quantize(_CENTAVO)),
        }
        chave = _chave_venda(registro, livros_por_id)
        if chave in chaves_vendas:
            ignorados += 1
            continue
        registro["id"] = proximo_id_venda
        proximo_id_venda += 1
        vendas_registros.append(registro)
        chaves_vendas.add(chave)
        novas_vendas.append(registro)

    livros_por_id, usuarios_por_id = _validar_relacionamentos(
        livros, usuarios_registros, emprestimos_registros, vendas_registros
    )
    consumo = {}
    for registro in novos_emprestimos:
        if registro["status"] == "emprestado":
            livro_id = registro["livro_id"]
            consumo[livro_id] = consumo.get(livro_id, 0) + 1
    for venda in novas_vendas:
        for item in venda["itens"]:
            livro_id = item["livro_id"]
            consumo[livro_id] = consumo.get(livro_id, 0) + item["quantidade"]

    for livro_id, quantidade in consumo.items():
        livro = livros_por_id[livro_id]
        if type(livro.get("quantidade")) is not int or livro["quantidade"] < quantidade:
            raise ValueError(
                f"Estoque insuficiente para aplicar os dados de demonstração ao livro ID {livro_id}."
            )
        livro["quantidade"] -= quantidade

    arquivos_alterados = {}
    if novos_livros or consumo:
        arquivos_alterados["livros.json"] = livros
    if novos_usuarios:
        arquivos_alterados["usuarios.json"] = usuarios_registros
    if novos_emprestimos:
        arquivos_alterados["emprestimos.json"] = emprestimos_registros
    if novas_vendas:
        arquivos_alterados["vendas.json"] = vendas_registros

    if arquivos_alterados:
        _salvar_transacionalmente(arquivos_alterados)

    print("=== POPULAÇÃO DE DADOS — LIVRARIA SABER ===\n")
    print(f"Livros adicionados: {len(novos_livros)}")
    print(f"Usuários adicionados: {len(novos_usuarios)}")
    print(f"Empréstimos adicionados: {len(novos_emprestimos)}")
    print(f"Vendas adicionadas: {len(novas_vendas)}")
    print(f"\nRegistros já existentes ignorados: {ignorados}")
    print("\nPopulação concluída com sucesso!")


def main():
    try:
        popular_dados()
    except (OSError, ValueError, RuntimeError) as erro:
        print(f"Falha na população dos dados: {erro}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
