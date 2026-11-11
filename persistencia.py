import json
from pathlib import Path


PASTA_PROJETO = Path(__file__).resolve().parent
PASTA_DADOS = PASTA_PROJETO / "dados"
NOMES_ARQUIVOS = (
    "livros.json",
    "usuarios.json",
    "emprestimos.json",
    "vendas.json",
)


def _obter_caminho(nome_arquivo):
    """Retorna o caminho de um dos arquivos de dados permitidos."""
    if nome_arquivo not in NOMES_ARQUIVOS:
        raise ValueError(f"Arquivo de dados não reconhecido: {nome_arquivo}")
    return PASTA_DADOS / nome_arquivo


def inicializar_arquivos():
    """Cria a pasta de dados e inicializa os arquivos ausentes com listas vazias."""
    try:
        PASTA_DADOS.mkdir(parents=True, exist_ok=True)

        for nome_arquivo in NOMES_ARQUIVOS:
            caminho = _obter_caminho(nome_arquivo)
            if not caminho.exists():
                with caminho.open("w", encoding="utf-8") as arquivo:
                    json.dump([], arquivo, indent=4, ensure_ascii=False)
    except OSError as erro:
        raise OSError(f"Não foi possível inicializar os arquivos de dados: {erro}") from erro


def carregar_dados(nome_arquivo):
    """Lê e retorna os dados de um arquivo JSON."""
    caminho = _obter_caminho(nome_arquivo)

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except json.JSONDecodeError as erro:
        raise ValueError(
            f"O arquivo {nome_arquivo} contém JSON inválido e não foi alterado."
        ) from erro
    except (OSError, UnicodeDecodeError) as erro:
        raise OSError(f"Não foi possível ler {nome_arquivo}: {erro}") from erro


def salvar_dados(nome_arquivo, dados):
    """Salva os dados em um arquivo JSON sem sobrescrever JSON inválido."""
    caminho = _obter_caminho(nome_arquivo)

    if caminho.exists():
        # Verifica primeiro se o conteúdo atual pode ser lido como JSON.
        carregar_dados(nome_arquivo)

    try:
        with caminho.open("w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, indent=4, ensure_ascii=False)
    except (OSError, TypeError, ValueError) as erro:
        raise OSError(f"Não foi possível salvar {nome_arquivo}: {erro}") from erro
