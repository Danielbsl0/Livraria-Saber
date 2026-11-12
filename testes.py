import contextlib
import importlib
import io
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import catalogo
import emprestimos
import livros
import main
import popular_dados
import persistencia
import usuarios
import vendas


class TestesLivrariaSaber(unittest.TestCase):
    def setUp(self):
        self.pasta_dados_original = persistencia.PASTA_DADOS
        self.diretorio_temporario = tempfile.TemporaryDirectory()
        persistencia.PASTA_DADOS = Path(self.diretorio_temporario.name) / "dados"
        persistencia.inicializar_arquivos()

    def tearDown(self):
        persistencia.PASTA_DADOS = self.pasta_dados_original
        self.diretorio_temporario.cleanup()

    def executar_com_entradas(self, funcao, entradas):
        saida = io.StringIO()
        with patch("builtins.input", side_effect=entradas):
            with contextlib.redirect_stdout(saida):
                funcao()
        return saida.getvalue()

    def salvar_livros_teste(self, registros=None):
        if registros is None:
            registros = [
                {
                    "id": 1,
                    "titulo": "Livro Um",
                    "autor": "Autora Um",
                    "editora": "Editora",
                    "genero": "Fantasia",
                    "ano_publicacao": 2020,
                    "isbn": "ISBN-1",
                    "preco": 10.25,
                    "quantidade": 8,
                },
                {
                    "id": 2,
                    "titulo": "Livro Dois",
                    "autor": "Autor Dois",
                    "editora": "Editora",
                    "genero": "Drama",
                    "ano_publicacao": 2021,
                    "isbn": "ISBN-2",
                    "preco": 3.10,
                    "quantidade": 4,
                },
            ]
        persistencia.salvar_dados("livros.json", registros)
        return registros

    def salvar_usuarios_teste(self, registros=None):
        if registros is None:
            registros = [
                {
                    "id": 1,
                    "cpf": "52998224725",
                    "nome": "Pessoa Um",
                    "telefone": "(82) 99999-0000",
                    "email": "pessoa@example.com",
                },
                {
                    "id": 2,
                    "cpf": "11144477735",
                    "nome": "Pessoa Dois",
                    "telefone": "",
                    "email": "",
                },
            ]
        persistencia.salvar_dados("usuarios.json", registros)
        return registros

    def criar_emprestimo(self, identificador=1, usuario_id=1, livro_id=1, status="emprestado"):
        devolucao = None if status == "emprestado" else date.today().isoformat()
        return {
            "id": identificador,
            "usuario_id": usuario_id,
            "livro_id": livro_id,
            "data_emprestimo": date.today().isoformat(),
            "data_prevista_devolucao": (date.today() + timedelta(days=7)).isoformat(),
            "data_devolucao": devolucao,
            "status": status,
        }

    def test_inicializacao_e_persistencia_json(self):
        for nome in persistencia.NOMES_ARQUIVOS:
            self.assertEqual(persistencia.carregar_dados(nome), [])
        conteudo = [{"nome": "Ação", "valor": 10}]
        persistencia.salvar_dados("livros.json", conteudo)
        self.assertEqual(persistencia.carregar_dados("livros.json"), conteudo)
        persistencia.salvar_dados("livros.json", [{"nome": "Atualizado"}])
        self.assertEqual(
            persistencia.carregar_dados("livros.json"), [{"nome": "Atualizado"}]
        )

    def test_populacao_em_base_vazia_preserva_referencias_e_atualiza_estoque(self):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            popular_dados.popular_dados()

        livros_salvos = persistencia.carregar_dados("livros.json")
        usuarios_salvos = persistencia.carregar_dados("usuarios.json")
        emprestimos_salvos = persistencia.carregar_dados("emprestimos.json")
        vendas_salvas = persistencia.carregar_dados("vendas.json")

        self.assertEqual(len(livros_salvos), 4)
        self.assertEqual(len(usuarios_salvos), 3)
        self.assertEqual(len(emprestimos_salvos), 2)
        self.assertEqual(len(vendas_salvas), 2)
        self.assertEqual([livro["id"] for livro in livros_salvos], [1, 2, 3, 4])
        self.assertEqual([usuario["id"] for usuario in usuarios_salvos], [1, 2, 3])
        self.assertEqual([registro["id"] for registro in emprestimos_salvos], [1, 2])
        self.assertEqual([registro["id"] for registro in vendas_salvas], [1, 2])
        self.assertEqual([livro["quantidade"] for livro in livros_salvos], [7, 5, 3, 7])
        self.assertEqual(
            {registro["status"] for registro in emprestimos_salvos},
            {"devolvido", "emprestado"},
        )
        livros_ids = {livro["id"] for livro in livros_salvos}
        usuarios_ids = {usuario["id"] for usuario in usuarios_salvos}
        for registro in emprestimos_salvos:
            self.assertIn(registro["livro_id"], livros_ids)
            self.assertIn(registro["usuario_id"], usuarios_ids)
        for venda in vendas_salvas:
            self.assertAlmostEqual(
                venda["total"],
                sum(item["quantidade"] * item["preco_unitario"] for item in venda["itens"]),
            )
            for item in venda["itens"]:
                self.assertIn(item["livro_id"], livros_ids)
        for usuario in usuarios_salvos:
            self.assertTrue(usuarios.validar_cpf(usuario["cpf"]))
        self.assertIn("Livros adicionados: 4", saida.getvalue())
        self.assertIn("População concluída com sucesso", saida.getvalue())

    def test_populacao_preserva_base_e_gera_ids_acima_do_maior(self):
        demo_livro = popular_dados._livros_demo()[0]
        livros_existentes = [
            {
                "id": 8,
                **demo_livro,
                "titulo": "  A BIBLIOTECA DAS ESTRELAS  ",
                "autor": "HELENA DUARTE",
                "quantidade": 10,
            },
            {
                "id": 20,
                "titulo": "Livro Preexistente",
                "autor": "Autor Preexistente",
                "editora": "Editora",
                "genero": "Drama",
                "ano_publicacao": 2020,
                "isbn": "ISBN-20",
                "preco": 15.0,
                "quantidade": 9,
            },
        ]
        usuarios_existentes = [
            {
                "id": 12,
                "cpf": "52998224725",
                "nome": "Usuário Preexistente",
                "telefone": "",
                "email": "",
            }
        ]
        emprestimo_existente = self.criar_emprestimo(
            identificador=30, usuario_id=12, livro_id=20, status="devolvido"
        )
        venda_existente = {
            "id": 40,
            "data_venda": "2026-10-01",
            "itens": [
                {
                    "livro_id": 20,
                    "titulo": "Livro Preexistente",
                    "quantidade": 1,
                    "preco_unitario": 15.0,
                }
            ],
            "total": 15.0,
        }
        persistencia.salvar_dados("livros.json", livros_existentes)
        persistencia.salvar_dados("usuarios.json", usuarios_existentes)
        persistencia.salvar_dados("emprestimos.json", [emprestimo_existente])
        persistencia.salvar_dados("vendas.json", [venda_existente])

        with contextlib.redirect_stdout(io.StringIO()):
            popular_dados.popular_dados()

        livros_salvos = persistencia.carregar_dados("livros.json")
        usuarios_salvos = persistencia.carregar_dados("usuarios.json")
        emprestimos_salvos = persistencia.carregar_dados("emprestimos.json")
        vendas_salvas = persistencia.carregar_dados("vendas.json")
        self.assertEqual(livros_salvos[0]["id"], 8)
        self.assertEqual(livros_salvos[0]["quantidade"], 9)
        self.assertEqual(livros_salvos[1], livros_existentes[1])
        self.assertEqual(usuarios_salvos[0], usuarios_existentes[0])
        self.assertEqual([livro["id"] for livro in livros_salvos[2:]], [21, 22, 23])
        self.assertEqual([usuario["id"] for usuario in usuarios_salvos[1:]], [13, 14, 15])
        self.assertEqual([item["id"] for item in emprestimos_salvos], [30, 31, 32])
        self.assertEqual([item["id"] for item in vendas_salvas], [40, 41, 42])
        self.assertEqual(emprestimos_salvos[0], emprestimo_existente)
        self.assertEqual(vendas_salvas[0], venda_existente)

    def test_populacao_nao_duplica_nem_desconta_estoque_novamente(self):
        with contextlib.redirect_stdout(io.StringIO()):
            popular_dados.popular_dados()
        conteudos_apos_primeira = {
            nome: (persistencia.PASTA_DADOS / nome).read_bytes()
            for nome in persistencia.NOMES_ARQUIVOS
        }

        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            popular_dados.popular_dados()

        self.assertIn("Registros já existentes ignorados: 11", saida.getvalue())
        for nome, conteudo in conteudos_apos_primeira.items():
            self.assertEqual((persistencia.PASTA_DADOS / nome).read_bytes(), conteudo)

    def test_populacao_preserva_arquivos_em_falha_de_leitura_ou_gravacao(self):
        caminhos = {
            nome: persistencia.PASTA_DADOS / nome
            for nome in persistencia.NOMES_ARQUIVOS
        }
        originais = {nome: caminho.read_bytes() for nome, caminho in caminhos.items()}
        caminhos["vendas.json"].write_text("{ JSON inválido", encoding="utf-8")
        corrompido = caminhos["vendas.json"].read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):
                popular_dados.popular_dados()
        for nome, caminho in caminhos.items():
            esperado = corrompido if nome == "vendas.json" else originais[nome]
            self.assertEqual(caminho.read_bytes(), esperado)

        for nome, conteudo in originais.items():
            caminhos[nome].write_bytes(conteudo)
        conteudos_antes_da_gravacao = {
            nome: caminho.read_bytes() for nome, caminho in caminhos.items()
        }
        salvar_original = persistencia.salvar_dados

        def falhar_ao_salvar_usuarios(nome, dados):
            if nome == "usuarios.json":
                raise OSError("falha simulada")
            salvar_original(nome, dados)

        with patch.object(persistencia, "salvar_dados", side_effect=falhar_ao_salvar_usuarios):
            with self.assertRaises(OSError):
                popular_dados.popular_dados()
        for nome, conteudo in conteudos_antes_da_gravacao.items():
            self.assertEqual(caminhos[nome].read_bytes(), conteudo)

    def test_json_invalido_e_falha_de_gravacao_preservam_arquivo(self):
        caminho = persistencia.PASTA_DADOS / "livros.json"
        caminho.write_text("{ JSON inválido", encoding="utf-8")
        conteudo_invalido = caminho.read_bytes()
        with self.assertRaises(ValueError):
            persistencia.salvar_dados("livros.json", [])
        self.assertEqual(caminho.read_bytes(), conteudo_invalido)

        caminho.write_text('[{"original": true}]', encoding="utf-8")
        conteudo_original = caminho.read_bytes()
        with patch.object(persistencia.json, "dump", side_effect=OSError("falha")):
            with self.assertRaises(OSError):
                persistencia.salvar_dados("livros.json", [{"novo": True}])
        self.assertEqual(caminho.read_bytes(), conteudo_original)
        self.assertEqual(list(persistencia.PASTA_DADOS.glob(".livros.json.*.tmp")), [])

    def test_carregadores_rejeitam_ids_duplicados_e_registros_invalidos(self):
        self.salvar_livros_teste(
            [
                {"id": 1, "titulo": "A", "autor": "X", "preco": 1, "quantidade": 1},
                {"id": 1, "titulo": "B", "autor": "Y", "preco": 1, "quantidade": 1},
            ]
        )
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertIsNone(livros.carregar_livros())

        self.salvar_usuarios_teste(
            [
                {"id": 1, "cpf": "52998224725", "nome": "A"},
                {"id": 1, "cpf": "11144477735", "nome": "B"},
            ]
        )
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertIsNone(usuarios.carregar_usuarios())

    def test_livros_cadastro_alteracao_exclusao(self):
        saida = self.executar_com_entradas(
            livros.cadastrar_livro,
            ["Livro Novo", "Autora", "Editora", "Fantasia", "2024", "ISBN-X", "19,90", "5"],
        )
        self.assertIn("Livro cadastrado com sucesso", saida)
        registro = persistencia.carregar_dados("livros.json")[0]
        self.assertEqual(registro["id"], 1)

        saida = self.executar_com_entradas(
            livros.alterar_livro,
            ["1", "Título Alterado", "", "", "", "", "", "22,50", "4"],
        )
        self.assertIn("Livro alterado com sucesso", saida)
        registro = persistencia.carregar_dados("livros.json")[0]
        self.assertEqual(registro["titulo"], "Título Alterado")
        self.assertEqual(registro["preco"], 22.5)

        saida = self.executar_com_entradas(livros.excluir_livro, ["1", "s"])
        self.assertIn("Livro excluído com sucesso", saida)
        self.assertEqual(persistencia.carregar_dados("livros.json"), [])

    def test_usuarios_cadastro_consulta_alteracao_exclusao_cpf(self):
        self.assertTrue(usuarios.validar_cpf("529.982.247-25"))
        self.assertFalse(usuarios.validar_cpf("111.111.111-11"))
        self.assertFalse(usuarios.validar_cpf("12345678900"))
        saida = self.executar_com_entradas(
            usuarios.cadastrar_usuario,
            ["529.982.247-25", "Pessoa Teste", "", ""],
        )
        self.assertIn("Usuário cadastrado com sucesso", saida)
        self.assertEqual(persistencia.carregar_dados("usuarios.json")[0]["cpf"], "52998224725")

        saida = self.executar_com_entradas(
            usuarios.cadastrar_usuario,
            ["52998224725"],
        )
        self.assertIn("Já existe", saida)
        saida = self.executar_com_entradas(usuarios.consultar_usuario, ["52998224725"])
        self.assertIn("Pessoa Teste", saida)

        saida = self.executar_com_entradas(
            usuarios.alterar_usuario,
            ["52998224725", "", "Nome Atualizado", "Telefone Atualizado", "email@exemplo.com"],
        )
        self.assertIn("Usuário alterado com sucesso", saida)
        atual = persistencia.carregar_dados("usuarios.json")[0]
        self.assertEqual(atual["id"], 1)
        self.assertEqual(atual["nome"], "Nome Atualizado")

        saida = self.executar_com_entradas(usuarios.excluir_usuario, ["1", "s"])
        self.assertIn("Usuário excluído com sucesso", saida)
        self.assertEqual(persistencia.carregar_dados("usuarios.json"), [])

    def test_catalogo_pesquisa_sem_alterar_json(self):
        self.salvar_livros_teste()
        caminho = persistencia.PASTA_DADOS / "livros.json"
        conteudo_original = caminho.read_bytes()
        saida = self.executar_com_entradas(catalogo.pesquisar_por_titulo, ["lIvRo uM"])
        self.assertIn("Livro Um", saida)
        saida = self.executar_com_entradas(catalogo.pesquisar_por_autor, ["AUTORA"])
        self.assertIn("Autora Um", saida)
        saida = self.executar_com_entradas(catalogo.pesquisar_por_genero, ["fant"])
        self.assertIn("Fantasia", saida)
        self.assertEqual(caminho.read_bytes(), conteudo_original)

    def test_emprestimo_devolucao_e_bloqueios_de_exclusao(self):
        self.salvar_livros_teste()
        self.salvar_usuarios_teste()
        data_prevista = (date.today() + timedelta(days=10)).strftime("%d/%m/%Y")
        saida = self.executar_com_entradas(
            emprestimos.registrar_emprestimo, ["1", "1", data_prevista]
        )
        self.assertIn("Empréstimo registrado com sucesso", saida)
        self.assertEqual(persistencia.carregar_dados("livros.json")[0]["quantidade"], 7)

        self.assertIn("não pode ser excluído", self.executar_com_entradas(livros.excluir_livro, ["1"]))
        self.assertIn("não pode ser excluído", self.executar_com_entradas(usuarios.excluir_usuario, ["1"]))

        saida = self.executar_com_entradas(emprestimos.registrar_devolucao, ["1", "s"])
        self.assertIn("Devolução registrada com sucesso", saida)
        self.assertEqual(persistencia.carregar_dados("livros.json")[0]["quantidade"], 8)
        saida = self.executar_com_entradas(emprestimos.registrar_devolucao, ["1"])
        self.assertIn("já foi devolvido", saida)

    def test_emprestimo_sem_estoque_e_cancelamento_de_devolucao(self):
        livros_teste = self.salvar_livros_teste()
        livros_teste[0]["quantidade"] = 0
        persistencia.salvar_dados("livros.json", livros_teste)
        self.salvar_usuarios_teste()
        data_prevista = (date.today() + timedelta(days=3)).strftime("%d/%m/%Y")
        saida = self.executar_com_entradas(
            emprestimos.registrar_emprestimo, ["1", "1", data_prevista]
        )
        self.assertIn("Não há exemplares disponíveis", saida)
        self.assertEqual(persistencia.carregar_dados("emprestimos.json"), [])

        persistencia.salvar_dados(
            "emprestimos.json", [self.criar_emprestimo()]
        )
        livros_teste[0]["quantidade"] = 2
        persistencia.salvar_dados("livros.json", livros_teste)
        antes = (persistencia.PASTA_DADOS / "livros.json").read_bytes()
        saida = self.executar_com_entradas(emprestimos.registrar_devolucao, ["1", "n"])
        self.assertIn("Devolução cancelada", saida)
        self.assertEqual((persistencia.PASTA_DADOS / "livros.json").read_bytes(), antes)

    def test_emprestimos_rejeitam_referencias_e_datas_invalidas(self):
        self.salvar_livros_teste()
        self.salvar_usuarios_teste()
        data_anterior = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")
        data_futura = (date.today() + timedelta(days=3)).strftime("%d/%m/%Y")

        saida = self.executar_com_entradas(
            emprestimos.registrar_emprestimo, ["99"]
        )
        self.assertIn("Não existe usuário", saida)
        saida = self.executar_com_entradas(
            emprestimos.registrar_emprestimo, ["1", "99"]
        )
        self.assertIn("Não existe livro", saida)
        saida = self.executar_com_entradas(
            emprestimos.registrar_emprestimo,
            ["1", "1", "31/02/2026", data_anterior, data_futura],
        )
        self.assertIn("Data inválida", saida)
        self.assertIn("não pode ser anterior", saida)
        self.assertIn("Empréstimo registrado com sucesso", saida)

    def test_menu_publico_catalogo_volta_ao_menu_principal(self):
        self.salvar_livros_teste()
        saida = self.executar_com_entradas(main.consultar_catalogo, ["1", "5"])
        self.assertIn("CATÁLOGO DE LIVROS", saida)
        self.assertIn("Livro Um", saida)

        saida = self.executar_com_entradas(main.main, ["1", "5", "3"])
        self.assertIn("Programa encerrado", saida)

    def test_venda_unica_multiplos_itens_repeticao_total_e_estoque(self):
        self.salvar_livros_teste()
        saida = self.executar_com_entradas(vendas.registrar_venda, ["1", "2", "s", "1", "1", "s", "2", "2", "n", "s"])
        self.assertIn("Venda registrada com sucesso", saida)
        venda = persistencia.carregar_dados("vendas.json")[0]
        self.assertEqual(len(venda["itens"]), 2)
        self.assertEqual(venda["itens"][0]["quantidade"], 3)
        self.assertEqual(venda["total"], 36.95)
        livros_salvos = persistencia.carregar_dados("livros.json")
        self.assertEqual(livros_salvos[0]["quantidade"], 5)
        self.assertEqual(livros_salvos[1]["quantidade"], 2)

    def test_venda_rejeita_quantidades_invalidas_e_preco_invalido(self):
        registros = self.salvar_livros_teste()
        saida = self.executar_com_entradas(
            vendas.registrar_venda,
            ["1", "0", "-1", "texto", "1", "n", "n"],
        )
        self.assertGreaterEqual(saida.count("quantidade inteira positiva"), 3)
        self.assertIn("Venda cancelada", saida)
        self.assertEqual(persistencia.carregar_dados("vendas.json"), [])

        registros.append(
            {
                "id": 3,
                "titulo": "Sem preço",
                "autor": "Autora",
                "editora": "",
                "genero": "",
                "ano_publicacao": None,
                "isbn": "",
                "preco": -1,
                "quantidade": 2,
            }
        )
        persistencia.salvar_dados("livros.json", registros)
        estoque_original = (persistencia.PASTA_DADOS / "livros.json").read_bytes()
        saida = self.executar_com_entradas(vendas.registrar_venda, [])
        self.assertIn("preço de cada livro deve ser finito", saida)
        self.assertIn("Venda cancelada", saida)
        self.assertEqual((persistencia.PASTA_DADOS / "livros.json").read_bytes(), estoque_original)
        self.assertEqual(persistencia.carregar_dados("vendas.json"), [])

    def test_venda_cancelada_estoque_insuficiente_e_rollback(self):
        self.salvar_livros_teste()
        caminho_livros = persistencia.PASTA_DADOS / "livros.json"
        caminho_vendas = persistencia.PASTA_DADOS / "vendas.json"
        livros_antes = caminho_livros.read_bytes()
        vendas_antes = caminho_vendas.read_bytes()
        saida = self.executar_com_entradas(vendas.registrar_venda, ["1", "1", "n", "n"])
        self.assertIn("Venda cancelada", saida)
        self.assertEqual(caminho_livros.read_bytes(), livros_antes)
        self.assertEqual(caminho_vendas.read_bytes(), vendas_antes)

        saida = self.executar_com_entradas(
            vendas.registrar_venda,
            ["1", "99", "1", "99", "1", "1", "n", "n"],
        )
        self.assertIn("Estoque insuficiente", saida)
        with patch.object(vendas, "_salvar_vendas", return_value=False):
            saida = self.executar_com_entradas(vendas.registrar_venda, ["1", "1", "n", "s"])
        self.assertIn("estoque anterior foi restaurado", saida)
        self.assertEqual(persistencia.carregar_dados("livros.json")[0]["quantidade"], 8)
        self.assertEqual(persistencia.carregar_dados("vendas.json"), [])

    def test_historico_vendas_preserva_snapshot_e_rejeita_dados_invalidos(self):
        self.salvar_livros_teste()
        saida = self.executar_com_entradas(vendas.registrar_venda, ["1", "1", "n", "s"])
        self.assertIn("Venda registrada com sucesso", saida)
        livros_salvos = persistencia.carregar_dados("livros.json")
        livros_salvos[0]["titulo"] = "Título Modificado"
        livros_salvos[0]["preco"] = 500
        persistencia.salvar_dados("livros.json", livros_salvos)
        historico = self.executar_com_entradas(vendas.listar_historico_vendas, [])
        self.assertIn("Livro Um", historico)
        self.assertIn("Preço unitário: R$ 10.25", historico)
        self.assertNotIn("Título Modificado", historico)

        persistencia.salvar_dados(
            "vendas.json",
            [
                {
                    "id": 1,
                    "data_venda": date.today().isoformat(),
                    "itens": [
                        {"livro_id": 1, "titulo": "Livro", "quantidade": 2, "preco_unitario": 3.0}
                    ],
                    "total": 3.0,
                }
            ],
        )
        saida = self.executar_com_entradas(vendas.listar_historico_vendas, [])
        self.assertIn("não corresponde", saida)

        venda_valida = {
            "id": 2,
            "data_venda": date.today().isoformat(),
            "itens": [
                {
                    "livro_id": 1,
                    "titulo": "Livro",
                    "quantidade": 1,
                    "preco_unitario": 3.0,
                }
            ],
            "total": 3.0,
        }
        persistencia.salvar_dados("vendas.json", [venda_valida, dict(venda_valida)])
        saida = self.executar_com_entradas(vendas.listar_historico_vendas, [])
        self.assertIn("IDs de venda duplicados", saida)

    def test_imports_e_menu_principal_integram_todas_as_areas(self):
        for modulo in (
            "main",
            "persistencia",
            "entradas",
            "livros",
            "usuarios",
            "catalogo",
            "emprestimos",
            "vendas",
        ):
            self.assertIsNotNone(importlib.import_module(modulo))

        chamadas = []
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(main, "menu_gerenciamento_livros", side_effect=lambda: chamadas.append("livros")))
            stack.enter_context(patch.object(main, "menu_gerenciamento_usuarios", side_effect=lambda: chamadas.append("usuarios")))
            stack.enter_context(patch.object(main, "menu_gerenciamento_emprestimos", side_effect=lambda: chamadas.append("emprestimos")))
            stack.enter_context(patch.object(main, "menu_gerenciamento_vendas", side_effect=lambda: chamadas.append("vendas")))
            stack.enter_context(patch("builtins.input", side_effect=["1", "2", "3", "4", "5"]))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            main.acessar_area_funcionario()
        self.assertEqual(chamadas, ["livros", "usuarios", "emprestimos", "vendas"])


if __name__ == "__main__":
    unittest.main()
