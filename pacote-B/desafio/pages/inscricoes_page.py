"""Page Object da tela de inscrições em minicursos (/inscricoes) - DESAFIO B.

Diferença importante para o Pacote A: esta página NÃO recarrega ao confirmar.
Um JavaScript envia os dados para a API e só troca o texto de #erro ou #sucesso.
Esses parágrafos sempre existem (vazios), então esperamos o TEXTO aparecer,
não o elemento. Os assert ficam nos testes.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait


class InscricoesPage:
    NOME = (By.ID, "nome")
    EMAIL = (By.ID, "email")
    CURSO = (By.ID, "curso")
    CONFIRMAR = (By.ID, "confirmar")
    ERRO = (By.ID, "erro")
    SUCESSO = (By.ID, "sucesso")
    ITENS_DA_LISTA = (By.CSS_SELECTOR, "#lista li")

    def __init__(self, driver, base_url):
        self.driver, self.base_url = driver, base_url
        self.wait = WebDriverWait(driver, 5)

    def abrir(self, itens_esperados=0):
        """Abre a tela e espera a lista carregar com a quantidade de inscrições já existentes."""
        self.driver.get(f"{self.base_url}/inscricoes")
        self.esperar_itens(itens_esperados)
        return self

    def inscrever(self, nome, email, curso=None):
        """Preenche o formulário e confirma. curso=None deixa em 'Selecione'."""
        campo_nome = self.driver.find_element(*self.NOME)
        campo_nome.clear()
        campo_nome.send_keys(nome)
        campo_email = self.driver.find_element(*self.EMAIL)
        campo_email.clear()
        campo_email.send_keys(email)
        if curso is not None:
            Select(self.driver.find_element(*self.CURSO)).select_by_value(str(curso))
        self.driver.find_element(*self.CONFIRMAR).click()

    def cancelar(self, id_inscricao):
        self.driver.find_element(By.CSS_SELECTOR, f"[data-testid='cancelar-{id_inscricao}']").click()

    def mensagem(self):
        """Espera aparecer texto em #erro ou em #sucesso e devolve esse texto."""
        def texto_na_tela(driver):
            erro = driver.find_element(*self.ERRO).text.strip()
            sucesso = driver.find_element(*self.SUCESSO).text.strip()
            return erro or sucesso      # string vazia = ainda não chegou -> continua esperando
        return self.wait.until(texto_na_tela)

    def itens(self):
        """Textos das inscrições na lista (ex.: 'Ana Souza / ana@ads.local / curso 1 Cancelar')."""
        return [li.text for li in self.driver.find_elements(*self.ITENS_DA_LISTA)]

    def esperar_itens(self, quantidade):
        """Espera a lista ter exatamente essa quantidade de inscrições e devolve os textos."""
        self.wait.until(lambda d: len(d.find_elements(*self.ITENS_DA_LISTA)) == quantidade)
        return self.itens()
