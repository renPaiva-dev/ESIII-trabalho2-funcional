"""Page Objects das duas telas do StockMaster: uma classe por tela.

Aqui ficam só os localizadores (id / data-testid) e as ações.
Os assert ficam nos testes.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

ESPERA = 10  # segundos


class ProdutosPage:
    NOME = (By.ID, "nome")
    DESCRICAO = (By.ID, "descricao")
    PRECO = (By.ID, "preco")
    QUANTIDADE = (By.ID, "quantidade")
    ESTOQUE_MINIMO = (By.ID, "estoque-minimo")
    CADASTRAR = (By.ID, "cadastrar")
    ERRO = (By.ID, "mensagem-erro")
    SUCESSO = (By.ID, "mensagem-sucesso")

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.espera = WebDriverWait(driver, ESPERA)

    def abrir(self):
        self.driver.get(self.base_url + "/produtos.html")
        self.espera.until(EC.visibility_of_element_located(self.NOME))
        return self

    def cadastrar(self, nome, preco, quantidade, estoque_minimo, descricao=""):
        for campo, valor in [(self.NOME, nome), (self.DESCRICAO, descricao), (self.PRECO, preco),
                             (self.QUANTIDADE, quantidade), (self.ESTOQUE_MINIMO, estoque_minimo)]:
            elemento = self.driver.find_element(*campo)
            elemento.clear()
            elemento.send_keys(valor)
        self.driver.find_element(*self.CADASTRAR).click()

    def mensagem(self):
        """Espera a API responder (erro ou sucesso aparece) e devolve (tipo, texto)."""
        self.espera.until(lambda d: d.find_element(*self.ERRO).text or d.find_element(*self.SUCESSO).text)
        erro = self.driver.find_element(*self.ERRO).text
        return ("erro", erro) if erro else ("sucesso", self.driver.find_element(*self.SUCESSO).text)

    def linha_do_produto(self, produto_id):
        """Espera a linha do produto aparecer na tabela e devolve as células como dicionário."""
        linha = self.espera.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, f"[data-testid='produto-{produto_id}']")))
        return {classe: linha.find_element(By.CLASS_NAME, classe).text
                for classe in ("id", "nome", "preco", "quantidade", "estoque-minimo")}

    def nomes_na_tabela(self):
        return [c.text for c in self.driver.find_elements(By.CSS_SELECTOR, "#lista-produtos td.nome")]


class VendaPage:
    PRODUTO = (By.ID, "produto")
    QUANTIDADE = (By.ID, "quantidade-item")
    ADICIONAR = (By.ID, "adicionar-item")
    CONFIRMAR = (By.ID, "confirmar-venda")
    ITENS = (By.CSS_SELECTOR, "#itens-venda tr")
    ERRO = (By.ID, "mensagem-erro")
    COMPROVANTE = (By.ID, "comprovante")
    VENDA_ID = (By.ID, "venda-id")
    VENDA_TOTAL = (By.ID, "venda-total")

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.espera = WebDriverWait(driver, ESPERA)

    def abrir(self, produtos_esperados=()):
        """Abre a tela e espera o select receber os produtos que o teste vai usar."""
        self.driver.get(self.base_url + "/venda.html")
        self.espera.until(EC.visibility_of_element_located(self.PRODUTO))
        for produto_id in produtos_esperados:
            self.espera.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, f"#produto option[value='{produto_id}']")))
        return self

    def adicionar_item(self, produto_id, quantidade):
        antes = len(self.driver.find_elements(*self.ITENS))
        Select(self.driver.find_element(*self.PRODUTO)).select_by_value(str(produto_id))
        campo = self.driver.find_element(*self.QUANTIDADE)
        campo.clear()
        campo.send_keys(str(quantidade))
        self.driver.find_element(*self.ADICIONAR).click()
        self.espera.until(lambda d: len(d.find_elements(*self.ITENS)) == antes + 1)

    def itens(self):
        return len(self.driver.find_elements(*self.ITENS))

    def confirmar(self):
        """Clica em confirmar e espera o comprovante OU a mensagem de erro."""
        self.driver.find_element(*self.CONFIRMAR).click()
        self.espera.until(lambda d: d.find_element(*self.COMPROVANTE).is_displayed()
                          or d.find_element(*self.ERRO).text)

    def mensagem_erro(self):
        return self.driver.find_element(*self.ERRO).text

    def comprovante_visivel(self):
        return self.driver.find_element(*self.COMPROVANTE).is_displayed()

    def numero_da_venda(self):
        return self.driver.find_element(*self.VENDA_ID).text

    def total(self):
        return self.driver.find_element(*self.VENDA_TOTAL).text

    def linha_do_comprovante(self, produto_id):
        linha = self.driver.find_element(By.CSS_SELECTOR, f"[data-testid='comprovante-produto-{produto_id}']")
        return {classe: linha.find_element(By.CLASS_NAME, classe).text
                for classe in ("nome", "quantidade", "preco-unitario", "subtotal")}
