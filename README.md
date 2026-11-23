# Trabalho 2 – Testes funcionais (ES III)

**Equipe:** Renato de Paiva Belarmino · Alisson Gabriel

Testes funcionais automatizados com **Selenium + pytest** (Page Objects e esperas explícitas) nos dois pacotes de
prática e no projeto anterior da equipe:

- **Pacote A:** Sabor Express e Matrícula.
- **Pacote B:** Biblioteca e Minicursos.
- **Projeto anterior:** StockMaster, com uma camada web mínima criada para os testes.

## Estrutura

```
trabalho2-funcional/
  README.md                      este arquivo
  pacote-A/
    exemplo/                     exemplo resolvido A (fluxo de pedido na lanchonete), código do professor
    desafio/                     desafio A (portal de matrícula): testes, Page Objects e matriz de casos
  pacote-B/
    exemplo/                     exemplo resolvido B (login no portal)
    desafio/                     desafio B (inscrições em minicursos): testes, Page Objects e matriz de casos
  projeto-anterior/              StockMaster: código do sistema, testes, Page Objects, matriz, defeitos e relatório
  resultados/                    relatórios HTML/XML das execuções e prints (evidências)
    pacote-A/exemplo/  pacote-A/desafio/  pacote-B/exemplo/  pacote-B/desafio/  projeto-anterior/
  relatorio.pdf
  slides.pdf
```

## Versões usadas

| Item | Versão |
|---|---|
| Python | 3.13.14 |
| Selenium | 4.53.0 (o Selenium Manager baixa o chromedriver sozinho) |
| pytest / pytest-html | 9.2.0 / 4.2.0 |
| Navegador | Google Chrome 157 |
| Flask (sistema do Pacote A) | 3.1.3 |
| Java / Maven (StockMaster) | JDK 21.0.6 (o projeto exige 17 ou superior) · Maven 3.9.11 · Spring Boot 3.5.15 |

## Preparação (uma vez)

Os sistemas dos pacotes A e B vêm no **kit do professor** (`ESIII_Testes_Funcionais_v2`). Abaixo, `KIT` é a pasta
onde o kit foi descompactado.

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1    |   Linux/macOS: source .venv/bin/activate
pip install "selenium>=4.25,<5" "pytest>=8,<10" "pytest-html>=4" "flask>=3.0"
```

- `HEADLESS=1` roda o Chrome sem janela. Foi assim que as execuções registradas foram feitas.
- No PowerShell, troque `VAR=valor comando` por `$env:VAR="valor"; comando`.
- **No Windows, use `127.0.0.1` em vez de `localhost`.** Com `localhost`, cada acesso perde cerca de 2 s tentando IPv6.
- **Rode cada suíte em sequência, nunca em paralelo.** O estado dos sistemas é compartilhado.

Para as **3 execuções** de cada desafio, rode o comando 3 vezes trocando `rN` por `r1`, `r2` e `r3`.

---

## Pacote A (sistema em `KIT/02_Pacote_A_SaborExpress_Matricula/app/app.py`, porta 5000)

```bash
python KIT/02_Pacote_A_SaborExpress_Matricula/app/app.py
```

### Exemplo resolvido A – Fluxo de pedido

```bash
cd pacote-A/exemplo
HEADLESS=1 BASE_URL=http://127.0.0.1:5000 python -m pytest -v --html=../../resultados/pacote-A/exemplo/relatorio_r1.html
```

Se um teste falhar, o print da tela vai para `evidencias/`. Os prints de uma execução com janela (sem `HEADLESS`), que
oscilou no Chrome 157, estão em `resultados/pacote-A/exemplo/evidencias/`. A mesma suíte passou inteira em headless.

### Desafio A – Portal de matrícula

Antes de cada teste, a fixture `sistema_zerado` zera o sistema sozinha (`POST /api/admin/reset`).

```bash
cd pacote-A/desafio
HEADLESS=1 BASE_URL=http://127.0.0.1:5000 python -m pytest test_matricula.py -v --html=../../resultados/pacote-A/desafio/relatorio_rN.html --self-contained-html
```

Matriz de casos: `pacote-A/desafio/matriz_casos.csv`.

---

## Pacote B (sistema em `KIT/03_Pacote_B_Biblioteca_Minicursos/app.py`, porta 8000)

```bash
python KIT/03_Pacote_B_Biblioteca_Minicursos/app.py
```

### Exemplo resolvido B – Login

```bash
cd pacote-B/exemplo
HEADLESS=1 python -m pytest test_login.py -v --junitxml=../../resultados/pacote-B/exemplo/resultado_login.xml
```

### Desafio B – Inscrições em minicursos

Antes de cada teste, a fixture `sistema_zerado` zera o sistema sozinha (`POST /api/reset`).

```bash
cd pacote-B/desafio
HEADLESS=1 python -m pytest test_inscricoes.py -v --html=../../resultados/pacote-B/desafio/relatorio_inscricoes_rN.html --self-contained-html
```

Matriz de casos: `pacote-B/desafio/matriz_casos_inscricoes.csv`.

---

## Projeto anterior – StockMaster (porta 8080)

O StockMaster não tinha interface web. Por isso foram criadas duas páginas mínimas, `produtos.html` e `venda.html`, em
`projeto-anterior/StockMaster/src/main/resources/static/`. Elas só chamam a API REST original. A justificativa está em
`projeto-anterior/relatorio_funcional_stockmaster.md`.

Requer JDK 17 ou superior e Maven instalado. O `mvnw` do projeto não funciona, porque a pasta `.mvn/` não existe no
repositório original.

```bash
cd projeto-anterior/StockMaster
mvn spring-boot:run              # deixe rodando; páginas em http://127.0.0.1:8080/produtos.html
```

Em outro terminal:

```bash
cd projeto-anterior
HEADLESS=1 python -m pytest test_stockmaster.py -v --html=../resultados/projeto-anterior/relatorio_stockmaster_rN.html --self-contained-html
```

- **CT13 falha de propósito:** ele demonstra o defeito DEF-01 (estoque negativo).
- **Matriz e defeitos:** `projeto-anterior/matriz_casos_stockmaster.csv` e `projeto-anterior/registro_defeitos_stockmaster.csv`.
- **Relatório:** `projeto-anterior/relatorio_funcional_stockmaster.md`.
