"""Page Objects do portal de Matrícula Acadêmica - DESAFIO A.

Telas: /matricula/login, /matricula/disciplinas e o comprovante.
Cada classe guarda os localizadores e as ações da sua tela; os assert ficam nos testes.
Só usamos id e data-testid, e esperas explícitas (WebDriverWait), nunca sleep.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class LoginMatriculaPage:
    MATRICULA = (By.ID, "matricula")
    SENHA = (By.ID, "senha")
    BOTAO_ENTRAR = (By.ID, "btn-entrar")
    MENSAGEM_ERRO = (By.ID, "mensagem-erro")   # aqui NÃO existe data-testid="erro"

    def __init__(self, driver, base_url):
        self.driver, self.base_url = driver, base_url
        self.wait = WebDriverWait(driver, 5)

    def abrir(self):
        self.driver.get(f"{self.base_url}/matricula/login")
        return self

    def entrar(self, matricula, senha):
        campo = self.wait.until(EC.visibility_of_element_located(self.MATRICULA))
        campo.clear()
        campo.send_keys(matricula)
        self.driver.find_element(*self.SENHA).send_keys(senha)
        self.driver.find_element(*self.BOTAO_ENTRAR).click()

    def mensagem_erro(self):
        return self.wait.until(EC.visibility_of_element_located(self.MENSAGEM_ERRO)).text


class DisciplinasPage:
    TABELA = (By.ID, "tabela-disciplinas")
    BOTAO_CONFIRMAR = (By.ID, "btn-confirmar")
    MENSAGEM_ERRO = (By.ID, "mensagem-erro")
    USUARIO_LOGADO = (By.ID, "usuario-logado")

    def __init__(self, driver, base_url):
        self.driver, self.base_url = driver, base_url
        self.wait = WebDriverWait(driver, 5)

    def abrir(self):
        self.driver.get(f"{self.base_url}/matricula/disciplinas")
        return self

    def esta_aberta(self):
        return self.wait.until(EC.visibility_of_element_located(self.TABELA)).is_displayed()

    def usuario_logado(self):
        return self.driver.find_element(*self.USUARIO_LOGADO).text

    def selecionar(self, *codigos):
        for codigo in codigos:
            caixa = self.wait.until(EC.element_to_be_clickable((By.ID, f"chk-{codigo}")))
            if not caixa.is_selected():
                caixa.click()
        return self

    def confirmar(self):
        self.driver.find_element(*self.BOTAO_CONFIRMAR).click()

    def mensagem_erro(self):
        return self.wait.until(EC.visibility_of_element_located(self.MENSAGEM_ERRO)).text

    def vagas(self, codigo):
        """Vagas restantes mostradas na linha da disciplina (data-testid='disc-<CODIGO>')."""
        celula = self.wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, f"[data-testid='disc-{codigo}'] .vagas")))
        return int(celula.text)


class ComprovantePage:
    MENSAGEM_SUCESSO = (By.ID, "mensagem-sucesso")
    COMPROVANTE = (By.ID, "comprovante")
    DISCIPLINAS = (By.ID, "disciplinas-matriculadas")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 5)

    def mensagem(self):
        return self.wait.until(EC.visibility_of_element_located(self.MENSAGEM_SUCESSO)).text

    def numero(self):
        return self.driver.find_element(*self.COMPROVANTE).text

    def disciplinas(self):
        """Lista de códigos mostrada no comprovante (ex.: ['ES3', 'BD2'])."""
        return self.driver.find_element(*self.DISCIPLINAS).text.split(", ")
