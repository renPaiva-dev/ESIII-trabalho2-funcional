"""Testes funcionais do projeto anterior (StockMaster) pela camada web mínima.

Fluxo 1: cadastro de produto (produtos.html)
Fluxo 2: venda (venda.html)

O StockMaster não tem rota de reset (banco H2 em memória). Para um teste não
depender do outro, cada teste cria pela API os próprios produtos com um sufixo
único no nome e só confere esses produtos. A ação avaliada e a verificação
principal são feitas pela tela; a API só prepara dados e confere o que foi gravado.
Rodar em sequência (sem -n / paralelo).
"""
import json
import re
import urllib.error
import urllib.request
import uuid

import pytest

from conftest import BASE_URL
from pages.stockmaster_pages import ProdutosPage, VendaPage


# ---------- apoio pela API (preparar estado e conferir o que foi gravado) ----------

def api(metodo, caminho, corpo=None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    pedido = urllib.request.Request(BASE_URL + caminho, data=dados, method=metodo,
                                    headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(pedido, timeout=10) as resposta:
            return resposta.status, json.loads(resposta.read() or b"null")
    except urllib.error.HTTPError as erro:
        return erro.code, json.loads(erro.read() or b"null")


def criar_produto(nome, preco, quantidade, estoque_minimo):
    status, corpo = api("POST", "/produtos", {"nome": nome, "preco": preco, "quantidade": quantidade,
                                              "estoqueMinimo": estoque_minimo, "descricao": "teste"})
    assert status == 201, corpo
    return corpo["id"]


def produtos_com_nome(nome):
    return [p for p in api("GET", "/produtos")[1] if p["nome"] == nome]


def estoque(produto_id):
    return api("GET", f"/produtos/{produto_id}")[1]["quantidade"]


def total_de_vendas():
    return len(api("GET", "/vendas")[1])


@pytest.fixture
def sufixo():
    return uuid.uuid4().hex[:6]


@pytest.fixture
def estoque_inicial(sufixo):
    """Dois produtos novos para cada teste de venda."""
    return {
        "caneta": criar_produto(f"Caneta-{sufixo}", 2.50, 30, 5),     # R$ 2,50, 30 em estoque
        "caderno": criar_produto(f"Caderno-{sufixo}", 10.00, 5, 1),   # R$ 10,00, 5 em estoque
    }


# ---------- Fluxo 1: cadastro de produto ----------

def test_ct01_cadastro_valido(driver, base_url, sufixo):
    nome = f"Caneta-{sufixo}"
    pagina = ProdutosPage(driver, base_url).abrir()

    pagina.cadastrar(nome, "2,50", "30", "5", descricao="Caneta azul")

    tipo, texto = pagina.mensagem()
    assert tipo == "sucesso"
    achado = re.fullmatch(rf"Produto cadastrado: {nome} \(ID (\d+)\)", texto)
    assert achado, texto
    linha = pagina.linha_do_produto(achado.group(1))
    assert linha == {"id": achado.group(1), "nome": nome, "preco": "2.50",
                     "quantidade": "30", "estoque-minimo": "5"}
    assert len(produtos_com_nome(nome)) == 1


def test_ct02_nome_obrigatorio(driver, base_url):
    antes = len(api("GET", "/produtos")[1])
    pagina = ProdutosPage(driver, base_url).abrir()

    pagina.cadastrar("", "2,50", "30", "5")

    tipo, texto = pagina.mensagem()
    assert tipo == "erro"
    assert texto == "nome: Nome é obrigatório"
    assert len(api("GET", "/produtos")[1]) == antes          # nada gravado


@pytest.mark.parametrize("preco, aceita", [("0,00", False), ("0,01", True)],
                         ids=["CT03a_preco_0.00", "CT03b_preco_0.01"])
def test_ct03_preco_valor_limite(driver, base_url, sufixo, preco, aceita):
    nome = f"Borracha-{sufixo}"
    pagina = ProdutosPage(driver, base_url).abrir()

    pagina.cadastrar(nome, preco, "10", "1")

    tipo, texto = pagina.mensagem()
    if aceita:
        assert tipo == "sucesso" and texto.startswith(f"Produto cadastrado: {nome}")
        assert len(produtos_com_nome(nome)) == 1
    else:
        assert tipo == "erro" and texto.startswith("preco: ")   # o texto vem do Bean Validation
        assert produtos_com_nome(nome) == []


@pytest.mark.parametrize("quantidade, aceita", [("-1", False), ("0", True)],
                         ids=["CT04a_quantidade_-1", "CT04b_quantidade_0"])
def test_ct04_quantidade_valor_limite(driver, base_url, sufixo, quantidade, aceita):
    nome = f"Regua-{sufixo}"
    pagina = ProdutosPage(driver, base_url).abrir()

    pagina.cadastrar(nome, "4,00", quantidade, "0")

    tipo, texto = pagina.mensagem()
    if aceita:
        assert tipo == "sucesso" and texto.startswith(f"Produto cadastrado: {nome}")
        assert len(produtos_com_nome(nome)) == 1
    else:
        assert tipo == "erro" and texto.startswith("quantidade: ")
        assert produtos_com_nome(nome) == []


def test_ct05_nome_duplicado(driver, base_url, sufixo):
    nome = f"Lapis-{sufixo}"
    criar_produto(nome, 1.00, 10, 1)
    pagina = ProdutosPage(driver, base_url).abrir()

    pagina.cadastrar(nome, "1,50", "3", "1")

    tipo, texto = pagina.mensagem()
    assert tipo == "erro"
    assert texto == f"Produto com nome '{nome}' já está cadastrado."
    assert len(produtos_com_nome(nome)) == 1                  # continua só o primeiro


# ---------- Fluxo 2: venda ----------

@pytest.mark.parametrize("canetas, cadernos, total", [
    (5, 4, "52.50"),   # 9 itens: sem desconto (12,50 + 40,00)
    (6, 4, "49.50"),   # 10 itens: 10% de desconto (55,00 - 5,50)
    (7, 4, "51.75"),   # 11 itens: 10% de desconto (57,50 - 5,75)
], ids=["CT06_9_itens_sem_desconto", "CT07a_10_itens_com_desconto", "CT07b_11_itens_com_desconto"])
def test_ct06_ct07_desconto_por_quantidade(driver, base_url, estoque_inicial, canetas, cadernos, total):
    caneta, caderno = estoque_inicial["caneta"], estoque_inicial["caderno"]
    pagina = VendaPage(driver, base_url).abrir([caneta, caderno])

    pagina.adicionar_item(caneta, canetas)
    pagina.adicionar_item(caderno, cadernos)
    pagina.confirmar()

    assert pagina.comprovante_visivel(), pagina.mensagem_erro()
    assert pagina.total() == total
    assert pagina.linha_do_comprovante(caneta)["subtotal"] == f"{canetas * 2.5:.2f}"
    assert pagina.linha_do_comprovante(caderno)["subtotal"] == f"{cadernos * 10:.2f}"
    assert estoque(caneta) == 30 - canetas and estoque(caderno) == 5 - cadernos


def test_ct08_estoque_insuficiente(driver, base_url, sufixo, estoque_inicial):
    caderno = estoque_inicial["caderno"]
    vendas_antes = total_de_vendas()
    pagina = VendaPage(driver, base_url).abrir([caderno])

    pagina.adicionar_item(caderno, 6)                         # só há 5
    pagina.confirmar()

    assert pagina.mensagem_erro() == (f"Estoque insuficiente para o produto 'Caderno-{sufixo}'. "
                                      "Quantidade disponível: 5")
    assert not pagina.comprovante_visivel()
    assert estoque(caderno) == 5 and total_de_vendas() == vendas_antes


def test_ct09_vender_todo_o_estoque(driver, base_url, estoque_inicial):
    caderno = estoque_inicial["caderno"]
    pagina = VendaPage(driver, base_url).abrir([caderno])

    pagina.adicionar_item(caderno, 5)                         # exatamente o estoque
    pagina.confirmar()

    assert pagina.comprovante_visivel(), pagina.mensagem_erro()
    assert pagina.total() == "50.00"
    assert estoque(caderno) == 0


def test_ct10_venda_atomica(driver, base_url, sufixo, estoque_inicial):
    caneta, caderno = estoque_inicial["caneta"], estoque_inicial["caderno"]
    vendas_antes = total_de_vendas()
    pagina = VendaPage(driver, base_url).abrir([caneta, caderno])

    pagina.adicionar_item(caneta, 2)                          # este item sozinho seria aceito
    pagina.adicionar_item(caderno, 6)                         # este não
    pagina.confirmar()

    assert pagina.mensagem_erro().startswith(f"Estoque insuficiente para o produto 'Caderno-{sufixo}'")
    assert estoque(caneta) == 30 and estoque(caderno) == 5    # nenhum estoque baixou
    assert total_de_vendas() == vendas_antes


def test_ct11_venda_sem_itens(driver, base_url, estoque_inicial):
    vendas_antes = total_de_vendas()
    pagina = VendaPage(driver, base_url).abrir([estoque_inicial["caneta"]])

    pagina.confirmar()                                        # nenhum item adicionado

    assert pagina.mensagem_erro() == "itens: A venda deve conter pelo menos um item"
    assert total_de_vendas() == vendas_antes


def test_ct12_quantidade_zero(driver, base_url, estoque_inicial):
    caneta = estoque_inicial["caneta"]
    vendas_antes = total_de_vendas()
    pagina = VendaPage(driver, base_url).abrir([caneta])

    pagina.adicionar_item(caneta, 0)
    pagina.confirmar()

    assert pagina.mensagem_erro() == "itens[0].quantidade: Quantidade deve ser maior que zero"
    assert estoque(caneta) == 30 and total_de_vendas() == vendas_antes


def test_ct13_mesmo_produto_em_duas_linhas(driver, base_url, sufixo, estoque_inicial):
    """Regra: a venda só é aceita se houver estoque para tudo o que foi pedido.
    3 + 3 cadernos = 6, mas só há 5. O esperado vem da regra, não do sistema."""
    caderno = estoque_inicial["caderno"]
    vendas_antes = total_de_vendas()
    pagina = VendaPage(driver, base_url).abrir([caderno])

    pagina.adicionar_item(caderno, 3)
    pagina.adicionar_item(caderno, 3)
    pagina.confirmar()

    # Se o sistema aceitar, a mensagem da falha mostra o que aconteceu (evidência do defeito)
    obtido = pagina.mensagem_erro() or (f"venda {pagina.numero_da_venda()} aceita, total R$ {pagina.total()}, "
                                        f"estoque do caderno agora = {estoque(caderno)}")
    assert obtido.startswith(f"Estoque insuficiente para o produto 'Caderno-{sufixo}'"), obtido
    assert estoque(caderno) == 5 and total_de_vendas() == vendas_antes
