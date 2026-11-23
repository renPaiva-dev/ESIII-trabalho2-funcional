"""
DESAFIO A - Trabalho 2: portal de Matrícula Acadêmica (Selenium + pytest)

Complete conforme o Guia do Aluno (Trabalho 2 > Desafio A): pelo menos 10 casos
especificados (R1 a R7) e pelo menos 8 automatizados aqui.

Sistema: python ../../../app/app.py   (http://localhost:5000/matricula/login)
Executar: pytest -v --html=relatorio.html     ($env:HEADLESS="1" para rodar sem janela)
"""
import json
import re
import pytest
import urllib.request # biblioteca python que faz requisicoes HTTP
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from pages.matricula_pages import ComprovantePage, DisciplinasPage, LoginMatriculaPage

ALUNO = "20260001"
SENHA = "senha123"
# vagas de cada disciplina logo depois do reset (DISCIPLINAS_BASE no app.py)
VAGAS_INICIAIS = {"ES3": 40, "BD2": 40, "PW2": 35, "RED": 30, "IHC": 30, "EMP": 50, "MOB": 5}


@pytest.fixture(autouse=True)
def sistema_zerado(base_url):
    # TODO: chamar POST {base_url}/api/admin/reset antes de cada teste (urllib.request ou requests)
    requisicao = urllib.request.Request(f"{base_url}/api/admin/reset", method="POST") # metodo post pra montar o pedido
    with urllib.request.urlopen(requisicao, timeout=5) as resposta:  # envia pedido e espera 5 segundos
        assert resposta.status == 200 #verifica se o servidor ta rodando


def test_ct01_login_valido(driver, base_url):
    LoginMatriculaPage(driver, base_url).abrir().entrar("20260001", "senha123")
    # TODO: entrar com 20260001 / senha123 e verificar que a oferta abriu
    oferta = DisciplinasPage(driver, base_url)
    assert oferta.esta_aberta() # confere no canto superior direito da tela se o usuario logado é o certo
    assert oferta.usuario_logado() == "20260001"


# TODO: demais casos (login inválido, acesso sem login, 0/1/5/6 disciplinas,
#       choque de horário, vagas esgotadas, matrícula repetida, vaga descontada...)

def matricular_pela_api(base_url, aluno, disciplinas):
    """POST /api/matriculas com JSON. Se não voltar 201, o urlopen levanta erro e o teste para."""
    corpo = json.dumps({"aluno": aluno, "disciplinas": disciplinas}).encode()
    requisicao = urllib.request.Request(f"{base_url}/api/matriculas", data=corpo, method="POST",
                                        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(requisicao, timeout=5) as resposta:
        assert resposta.status == 201


def ocupar_vagas(base_url, codigo, quantidade):
    """Matricula outros alunos (20260101, 20260102, ...) na disciplina para gastar as vagas."""
    for n in range(quantidade):
        matricular_pela_api(base_url, f"2026{101 + n:04d}", [codigo])


def rejeicao_nao_gravou_matricula(driver, oferta):
    """Prova, pela tela, de que a matrícula recusada não ficou gravada.

    R6 só permite uma matrícula por aluno. Então, logo depois da recusa, o mesmo
    aluno tenta uma matrícula válida (IHC, QUI-19h, sem choque com nada). Se o
    comprovante aparecer, não existia matrícula dele. Fica no fim do teste porque
    muda o estado; o reset do próximo teste limpa tudo.
    """
    oferta.selecionar("IHC").confirmar()
    return ComprovantePage(driver).foi_exibido()


@pytest.fixture
def oferta(driver, base_url):
    """Pré-condição comum: aluno 20260001 logado e vendo a oferta de disciplinas."""
    LoginMatriculaPage(driver, base_url).abrir().entrar(ALUNO, SENHA)
    pagina = DisciplinasPage(driver, base_url)
    assert pagina.esta_aberta()
    return pagina


@pytest.mark.parametrize("matricula, senha", [
    pytest.param(ALUNO, "senhaerrada", id="senha_errada"),
    pytest.param("20260201", SENHA, id="matricula_inexistente"),   # logo acima do último aluno
    pytest.param("", "", id="campos_vazios"),
])
def test_ct02_login_invalido(driver, base_url, matricula, senha):
    login = LoginMatriculaPage(driver, base_url).abrir()
    login.entrar(matricula, senha)
    assert login.mensagem_erro() == "Matrícula ou senha inválidas."
    assert driver.current_url.endswith("/matricula/login")         # não entrou


def test_ct03_oferta_exige_login(driver, base_url):
    DisciplinasPage(driver, base_url).abrir() # tenta ir direto na oferta
    WebDriverWait(driver, 5).until(EC.url_contains("/matricula/login"))
    assert driver.find_elements(*DisciplinasPage.TABELA) == [] # a oferta não apareceu


def test_ct04_nenhuma_disciplina(driver, oferta):
    oferta.confirmar()                                              # confirma sem marcar nada
    assert oferta.mensagem_erro() == "Selecione ao menos uma disciplina."
    assert oferta.quadro_de_vagas(VAGAS_INICIAIS) == VAGAS_INICIAIS   # nenhuma vaga descontada
    assert rejeicao_nao_gravou_matricula(driver, oferta)            # e nenhuma matrícula gravada


@pytest.mark.parametrize("codigos", [
    pytest.param(["ES3"], id="1_disciplina"),
    pytest.param(["ES3", "BD2", "PW2", "IHC", "EMP"], id="5_disciplinas"),
])
def test_ct05_quantidade_valida(driver, oferta, codigos):
    oferta.selecionar(*codigos).confirmar()
    comprovante = ComprovantePage(driver)
    assert comprovante.mensagem() == "Matrícula realizada com sucesso!"
    assert comprovante.disciplinas() == codigos


def test_ct06_seis_disciplinas(driver, oferta):
    seis = ["ES3", "BD2", "PW2", "IHC", "EMP", "MOB"]   # sem choque entre elas: só a quantidade falha
    oferta.selecionar(*seis).confirmar()
    assert oferta.mensagem_erro() == "Máximo de 5 disciplinas por semestre."
    assert oferta.quadro_de_vagas(VAGAS_INICIAIS) == VAGAS_INICIAIS   # nenhuma vaga descontada
    assert rejeicao_nao_gravou_matricula(driver, oferta)


def test_ct07_choque_de_horario(driver, oferta):
    oferta.selecionar("ES3", "RED").confirmar()        # as duas são SEG-19h
    assert oferta.mensagem_erro() == "Choque de horário entre disciplinas selecionadas."
    assert oferta.quadro_de_vagas(VAGAS_INICIAIS) == VAGAS_INICIAIS   # nada gravado (ES3 40, RED 30...)
    assert rejeicao_nao_gravou_matricula(driver, oferta)


def test_ct08_vagas_esgotadas(driver, base_url):
    ocupar_vagas(base_url, "MOB", 5)                   # MOB tem 5 vagas: lota pela API
    LoginMatriculaPage(driver, base_url).abrir().entrar(ALUNO, SENHA)
    oferta = DisciplinasPage(driver, base_url)
    assert oferta.vagas("MOB") == 0
    oferta.selecionar("MOB", "ES3").confirmar()
    assert oferta.mensagem_erro() == "Vagas esgotadas: MOB."
    assert oferta.quadro_de_vagas(VAGAS_INICIAIS) == dict(VAGAS_INICIAIS, MOB=0)   # ES3 não foi descontada (tudo ou nada)
    assert rejeicao_nao_gravou_matricula(driver, oferta)


def test_ct09_ultima_vaga(driver, base_url):
    ocupar_vagas(base_url, "MOB", 4)   # sobra exatamente 1 vaga
    LoginMatriculaPage(driver, base_url).abrir().entrar(ALUNO, SENHA)
    oferta = DisciplinasPage(driver, base_url)
    assert oferta.vagas("MOB") == 1
    oferta.selecionar("MOB").confirmar()
    assert ComprovantePage(driver).mensagem() == "Matrícula realizada com sucesso!"
    assert DisciplinasPage(driver, base_url).abrir().vagas("MOB") == 0



def test_ct10_matricula_repetida(driver, base_url):
    matricular_pela_api(base_url, ALUNO, ["BD2"])      # o aluno já tem matrícula
    LoginMatriculaPage(driver, base_url).abrir().entrar(ALUNO, SENHA)
    oferta = DisciplinasPage(driver, base_url)
    oferta.selecionar("ES3").confirmar()
    assert oferta.mensagem_erro() == "Aluno já possui matrícula neste semestre."
    assert oferta.vagas("ES3") == 40          # nada gravado



def test_ct11_matricula_com_sucesso(driver, base_url, oferta):
    oferta.selecionar("ES3", "BD2").confirmar()
    comprovante = ComprovantePage(driver)
    assert comprovante.mensagem() == "Matrícula realizada com sucesso!"
    assert re.fullmatch(r"COMP-\d{6}", comprovante.numero()) # COMP- + 6 dígitos
    assert comprovante.disciplinas() == ["ES3", "BD2"]
    nova_oferta = DisciplinasPage(driver, base_url).abrir() # volta para a oferta
    # 1 vaga a menos em ES3 e BD2, e todas as outras disciplinas iguais
    assert nova_oferta.quadro_de_vagas(VAGAS_INICIAIS) == dict(VAGAS_INICIAIS, ES3=39, BD2=39)
