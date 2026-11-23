"""
DESAFIO B - Trabalho 2: inscrições em minicursos (Selenium + pytest)

Casos especificados em matriz_casos_inscricoes.csv (CT01 a CT12).

Sistema: python app.py   (http://127.0.0.1:8000/inscricoes)
Executar (da pasta 03_Pacote_B_Biblioteca_Minicursos, sempre em sequência):
    python -m pytest funcionais/test_inscricoes.py -v --html=relatorio_inscricoes_r1.html --self-contained-html

Cada teste começa com POST /api/reset. O estado que a tela não monta rápido
(aluna já inscrita, curso lotado) é preparado por POST /api/inscricoes;
a ação avaliada e a mensagem são verificadas pela tela.
"""
import json
import os
import urllib.request

import pytest

from pages.inscricoes_page import InscricoesPage

BASE = os.getenv("BASE_URL", "http://127.0.0.1:8000")
NOME_DE_ERRO = "Nome deve ter de 3 a 60 caracteres"


# ---------------------------------------------------------------------------
# Preparação e conferência pela API
# ---------------------------------------------------------------------------
def api(metodo, caminho, corpo=None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    requisicao = urllib.request.Request(f"{BASE}{caminho}", data=dados, method=metodo,
                                        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(requisicao, timeout=5) as resposta:
        return json.loads(resposta.read())


def inscrever_pela_api(nome, email, curso):
    api("POST", "/api/inscricoes", {"nome": nome, "email": email, "curso": curso})


def inscricoes_gravadas():
    """O que o servidor guardou (consulta pela API)."""
    return api("GET", "/api/inscricoes")["itens"]


def conferir_lista(pagina, quantidade):
    """Confere que ficaram gravadas exatamente `quantidade` inscrições.

    1. Pela API: o que o servidor guardou.
    2. Pela tela: depois de um erro a página não atualiza a lista sozinha, então
       recarregamos e esperamos a lista mostrar a mesma quantidade.
    Com quantidade 0 a conferência da tela é fraca (a lista começa vazia antes de
    carregar); nesse caso a prova principal é a da API.
    """
    assert len(inscricoes_gravadas()) == quantidade
    itens = pagina.abrir(itens_esperados=quantidade).itens()
    assert len(itens) == quantidade
    return itens


@pytest.fixture(autouse=True)
def sistema_zerado():
    api("POST", "/api/reset", {})


@pytest.fixture
def pagina(driver):
    return InscricoesPage(driver, BASE)


# ---------------------------------------------------------------------------
# Fluxos válidos
# ---------------------------------------------------------------------------
def test_ct01_inscricao_valida(pagina):
    pagina.abrir()
    pagina.inscrever("Ana Souza", "ana@ads.local", 1)
    assert pagina.mensagem() == "Inscrição realizada"
    itens = pagina.esperar_itens(1)
    assert "ana@ads.local" in itens[0]


def test_ct02_mesmo_email_em_outro_curso(pagina):
    inscrever_pela_api("Ana Souza", "ana@ads.local", 1)
    pagina.abrir(itens_esperados=1)
    pagina.inscrever("Ana Souza", "ana@ads.local", 2)
    assert pagina.mensagem() == "Inscrição realizada"
    itens = pagina.esperar_itens(2)
    assert "curso 2" in itens[1]


# ---------------------------------------------------------------------------
# Obrigatórios e formato
# ---------------------------------------------------------------------------
def test_ct03_nome_vazio(pagina):
    pagina.abrir()
    pagina.inscrever("", "ana@ads.local", 1)
    assert pagina.mensagem() == NOME_DE_ERRO
    conferir_lista(pagina, 0)


def test_ct04_email_invalido(pagina):
    pagina.abrir()
    pagina.inscrever("Ana Souza", "ana@ads", 1)          # domínio sem ponto
    assert pagina.mensagem() == "E-mail inválido"
    conferir_lista(pagina, 0)


def test_ct05_curso_ausente(pagina):
    pagina.abrir()
    pagina.inscrever("Ana Souza", "ana@ads.local")       # curso fica em "Selecione"
    assert pagina.mensagem() == "Curso obrigatório"
    conferir_lista(pagina, 0)


# ---------------------------------------------------------------------------
# Valores-limite do nome (teste orientado a dados)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nome, mensagem_esperada, gravadas", [
    pytest.param("Al", NOME_DE_ERRO, 0, id="2_caracteres"),
    pytest.param("Ana", "Inscrição realizada", 1, id="3_caracteres"),
    pytest.param("A" * 60, "Inscrição realizada", 1, id="60_caracteres"),
    pytest.param("A" * 61, NOME_DE_ERRO, 0, id="61_caracteres"),
])
def test_ct06_a_ct09_tamanho_do_nome(pagina, nome, mensagem_esperada, gravadas):
    pagina.abrir()
    pagina.inscrever(nome, "ana@ads.local", 1)
    assert pagina.mensagem() == mensagem_esperada
    conferir_lista(pagina, gravadas)


# ---------------------------------------------------------------------------
# Regras com estado
# ---------------------------------------------------------------------------
def test_ct10_duplicidade_com_maiusculas_e_espacos(pagina):
    inscrever_pela_api("Ana Souza", "ana@ads.local", 1)
    pagina.abrir(itens_esperados=1)
    pagina.inscrever("Ana Souza", "  ANA@ADS.LOCAL  ", 1)  # mesmo e-mail depois de normalizar
    assert pagina.mensagem() == "Inscrição já existente"
    conferir_lista(pagina, 1)                              # continua só a inscrição original


def test_ct11_lotacao(pagina):
    inscrever_pela_api("Bruno Reis", "bruno@ads.local", 1)
    inscrever_pela_api("Dani Costa", "dani@ads.local", 1)   # Python lotado (2 vagas)
    pagina.abrir(itens_esperados=2)
    pagina.inscrever("Carla Lima", "carla@ads.local", 1)
    assert pagina.mensagem() == "Curso sem vagas"
    itens = conferir_lista(pagina, 2)
    assert not any("carla@ads.local" in item for item in itens)   # Carla não entrou


def test_ct12_cancelamento_libera_vaga(pagina):
    inscrever_pela_api("Bruno Reis", "bruno@ads.local", 1)  # id 1
    inscrever_pela_api("Dani Costa", "dani@ads.local", 1)   # id 2 -> Python lotado
    pagina.abrir(itens_esperados=2)

    pagina.cancelar(1)
    assert pagina.mensagem() == "Inscrição cancelada"
    itens = pagina.esperar_itens(1)
    assert "bruno@ads.local" not in itens[0]

    pagina.inscrever("Carla Lima", "carla@ads.local", 1)    # a vaga liberada pode ser usada
    assert pagina.mensagem() == "Inscrição realizada"
    itens = pagina.esperar_itens(2)
    assert any("carla@ads.local" in item for item in itens)
