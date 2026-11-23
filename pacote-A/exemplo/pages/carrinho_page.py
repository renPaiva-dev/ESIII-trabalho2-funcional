"""Page Objects do carrinho e da confirmação do pedido."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


class CarrinhoPage:
    TOTAL = (By.ID, "total")
    ENDERECO = (By.ID, "endereco")
    PAGAMENTO = (By.ID, "pagamento")
    BOTAO_FINALIZAR = (By.ID, "btn-finalizar")
    MENSAGEM_ERRO = (By.ID, "mensagem-erro")
    CARRINHO_VAZIO = (By.ID, "carrinho-vazio")
    LINHAS_ITENS = (By.CSS_SELECTOR, "#tabela-carrinho tr")

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 5)

    def abrir(self):
        self.driver.get(f"{self.base_url}/carrinho")
        return self

    def total(self):
        return self.wait.until(EC.visibility_of_element_located(self.TOTAL)).text

    def quantidade_de_linhas(self):
        return len(self.driver.find_elements(*self.LINHAS_ITENS)) - 1  # desconta o cabeçalho

    def finalizar(self, endereco="", pagamento=""):
        campo = self.wait.until(EC.visibility_of_element_located(self.ENDERECO))
        campo.clear()
        campo.send_keys(endereco)
        if pagamento:
            Select(self.driver.find_element(*self.PAGAMENTO)).select_by_value(pagamento)
        self.driver.find_element(*self.BOTAO_FINALIZAR).click()

    def mensagem_erro(self):
        return self.wait.until(EC.visibility_of_element_located(self.MENSAGEM_ERRO)).text

    def esta_vazio(self):
        return self.wait.until(EC.visibility_of_element_located(self.CARRINHO_VAZIO)).is_displayed()


class ConfirmacaoPage:
    MENSAGEM_SUCESSO = (By.ID, "mensagem-sucesso")
    TOTAL = (By.ID, "total-pedido")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 5)

    def mensagem(self):
        return self.wait.until(EC.visibility_of_element_located(self.MENSAGEM_SUCESSO)).text

    def total(self):
        return self.driver.find_element(*self.TOTAL).text
