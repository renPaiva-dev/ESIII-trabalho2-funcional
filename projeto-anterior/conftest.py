"""
Configuração compartilhada do pytest (mesmo modelo do exemplo do professor).

Variáveis de ambiente opcionais:
    BASE_URL  -> endereço do StockMaster (padrão http://127.0.0.1:8080)
    HEADLESS  -> "1" para rodar sem abrir a janela do navegador
"""
import os
import pathlib

import pytest
from selenium import webdriver

# 127.0.0.1 e não localhost: no Windows, "localhost" tenta IPv6 primeiro e atrasa ~2 s.
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8080")


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def driver(request):
    opcoes = webdriver.ChromeOptions()
    if os.getenv("HEADLESS") == "1":
        opcoes.add_argument("--headless=new")
    opcoes.add_argument("--window-size=1280,900")
    drv = webdriver.Chrome(options=opcoes)
    drv.implicitly_wait(0)  # só esperas EXPLÍCITAS (WebDriverWait)
    yield drv
    # Se o teste falhou, salva um print da tela como evidência do defeito
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        pasta = pathlib.Path(__file__).parent / "evidencias"
        pasta.mkdir(exist_ok=True)
        drv.save_screenshot(str(pasta / f"{request.node.name}.png"))
    drv.quit()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Guarda o resultado de cada fase do teste para a fixture 'driver' consultar."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
