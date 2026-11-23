"""Page Objects do portal de Matrícula Acadêmica - DESAFIO A.

Telas: /matricula/login, /matricula/disciplinas e o comprovante.
Cada classe guarda os localizadores e as ações da sua tela; os assert ficam nos testes.
Só usamos id e data-testid, e esperas explícitas (WebDriverWait), nunca sleep.
"""
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def esperar_pagina_nova(driver, botao):
    """Espera o botão clicado sumir, ou seja, a página antiga ser trocada pela nova.

    staleness_of é a espera que o exemplo do professor usa. O Chrome 157 às vezes
    devolve um erro genérico no meio da troca de página ("Node with given id does
    not belong to the document"); com ignored_exceptions o WebDriverWait ignora
    esse erro e pergunta de novo, em vez de derrubar o teste.
    """
    WebDriverWait(driver, 5, ignored_exceptions=[WebDriverException]).until(EC.staleness_of(botao))


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
        botao = self.driver.find_element(*self.BOTAO_ENTRAR)
        botao.click()
        esperar_pagina_nova(self.driver, botao)   # o servidor responde com uma página nova

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
        botao = self.wait.until(EC.element_to_be_clickable(self.BOTAO_CONFIRMAR))
        botao.click()
        esperar_pagina_nova(self.driver, botao)   # comprovante ou oferta com erro

    def mensagem_erro(self):
        return self.wait.until(EC.visibility_of_element_located(self.MENSAGEM_ERRO)).text

    def vagas(self, codigo):
        """Vagas restantes mostradas na linha da disciplina (data-testid='disc-<CODIGO>')."""
        celula = self.wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, f"[data-testid='disc-{codigo}'] .vagas")))
        return int(celula.text)

    def quadro_de_vagas(self, codigos):
        """Vagas de várias disciplinas de uma vez, ex.: {'ES3': 40, 'BD2': 40, ...}."""
        return {codigo: self.vagas(codigo) for codigo in codigos}


class ComprovantePage:
    MENSAGEM_SUCESSO = (By.ID, "mensagem-sucesso")
    COMPROVANTE = (By.ID, "comprovante")
    DISCIPLINAS = (By.ID, "disciplinas-matriculadas")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 5)

    def mensagem(self):
        return self.wait.until(EC.visibility_of_element_located(self.MENSAGEM_SUCESSO)).text

    def foi_exibido(self):
        """True se a tela atual é o comprovante. Sem espera: use depois de confirmar(),
        que já aguardou a página nova carregar."""
        return len(self.driver.find_elements(*self.MENSAGEM_SUCESSO)) == 1

    def numero(self):
        return self.driver.find_element(*self.COMPROVANTE).text

    def disciplinas(self):
        """Lista de códigos mostrada no comprovante (ex.: ['ES3', 'BD2'])."""
        return self.driver.find_element(*self.DISCIPLINAS).text.split(", ")
