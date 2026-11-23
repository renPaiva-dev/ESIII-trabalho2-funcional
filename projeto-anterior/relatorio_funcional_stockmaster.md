# Testes funcionais – Projeto anterior (StockMaster)

Equipe: Renato de Paiva Belarmino, Alisson Gabriel · Data das execuções: 22/11/2026

## 1. Sistema e adaptação feita

O StockMaster é o sistema de controle de estoque e vendas da equipe, feito em ES II
(Java 17, Spring Boot 3.5.15, banco H2 em memória). Ele **não tinha interface web**: toda a
interação era pela API REST.

Como o guia permite ("Se o projeto não for web, combinar com o professor uma camada web
mínima ligada ao código original"), foram criadas duas páginas estáticas em
`StockMaster/src/main/resources/static/`, servidas pelo próprio Spring:

| Página | O que faz | API original chamada |
|---|---|---|
| `produtos.html` | cadastra produto e lista os produtos | `POST /produtos`, `GET /produtos` |
| `venda.html` | monta a venda item a item, confirma e mostra o comprovante | `GET /produtos`, `POST /vendas` |

As páginas **não têm regra de negócio**: só enviam os dados para a API e mostram o que o
Java devolveu (mensagem de sucesso, comprovante ou mensagem de erro). Assim, o que os
testes verificam são as regras do código original. Todos os elementos usados pelos testes
têm `id` ou `data-testid`. Por exemplo: `#nome`, `#cadastrar`, `#mensagem-erro`,
`[data-testid='produto-7']`, `#confirmar-venda`, `#venda-total` e
`[data-testid='comprovante-produto-7']`.

Também foi preciso corrigir um erro que impedia o projeto de compilar (DEF-04, abaixo).

## 2. Regras cobertas

| Regra | Origem no código |
|---|---|
| R1 – Campos do produto: nome obrigatório; preço ≥ 0,01; quantidade ≥ 0; estoque mínimo ≥ 0 | `ProdutoRequestDTO` (Bean Validation) |
| R2 – Nome de produto único | `ProdutoService` → `ProdutoJaCadastradoException` (409) |
| R3 – Venda só com estoque suficiente para tudo; se um item falha, nada é baixado (RN05) | `VendaService.registrarVenda` |
| R4 – Desconto de 10% quando a venda soma 10 itens ou mais | `DescontoPorQuantidadeStrategy` |
| R5 – Venda com pelo menos 1 item e quantidade ≥ 1 | `VendaRequestDTO`, `ItemVendaRequestDTO` |

## 3. Matriz de casos

A matriz completa está em `matriz_casos_stockmaster.csv` (16 linhas, CT01 a CT13). Os casos cobrem os dois fluxos pedidos:
- **Cadastro de produto:** CT01 a CT05.
- **Venda:** CT06 a CT13.

| Técnica | Casos |
|---|---|
| Partição de equivalência | CT01 (válido), CT02 (nome vazio), CT11 (venda sem itens) |
| Valor-limite | CT03a/b (preço 0,00 / 0,01), CT04a/b (quantidade −1 / 0), CT08 (estoque + 1), CT09 (= estoque), CT12 (quantidade 0) |
| Tabela de decisão | CT06 / CT07a / CT07b (9, 10 e 11 itens → sem/com desconto), CT10 (um item ok e outro sem estoque) |
| Regra com estado | CT05 (nome já cadastrado), CT13 (mesmo produto em duas linhas) |

O resultado esperado foi tirado da regra, não do que o sistema mostra. Por isso o CT13
espera a recusa da venda (3 + 3 = 6 cadernos com só 5 em estoque), e ele falha.

## 4. Estrutura do código

```
projeto-anterior/
  StockMaster/                 código do sistema (com produtos.html e venda.html em src/main/resources/static/)
  conftest.py                  fixture driver (Chrome; HEADLESS=1), print automático na falha
  pages/stockmaster_pages.py   Page Objects: ProdutosPage e VendaPage (localizadores + ações)
  test_stockmaster.py          os casos (os assert ficam aqui)
  matriz_casos_stockmaster.csv
  registro_defeitos_stockmaster.csv
resultados/projeto-anterior/
  relatorio_stockmaster_r1..r3.html   relatórios das 3 execuções (pytest-html)
  evidencias/                  print do CT13 e respostas da API dos defeitos 02 e 03
```

- **Page Objects:** uma classe por tela. As ações esperam a resposta da API antes de devolver o controle. Por exemplo, `mensagem()` espera aparecer texto no erro ou no sucesso, e `confirmar()` espera o comprovante ou o erro.
- **Esperas:** só `WebDriverWait`, sem `sleep` e com `implicitly_wait(0)`. As esperas são necessárias porque as páginas carregam a lista e enviam o formulário com `fetch` (assíncrono). Sem elas, o teste leria a tela antes da resposta chegar.
- **Dados de teste:** o StockMaster não tem rota de reset e o banco é em memória. Por isso cada teste cria os próprios produtos pela API, com um sufixo aleatório no nome (`Caneta-1a69b7`), e só confere esses produtos. Assim os testes não dependem um do outro nem da ordem. A ação avaliada e a verificação principal são sempre feitas pela tela. A API só prepara os dados e confere que nada foi gravado indevidamente (contagem de produtos, estoque e número de vendas).

## 5. Resultado das 3 execuções

Comando (StockMaster rodando em `http://127.0.0.1:8080`, reiniciado antes da 1ª execução):

```
HEADLESS=1 python -m pytest test_stockmaster.py -v --html=../resultados/projeto-anterior/relatorio_stockmaster_rN.html --self-contained-html
```

| Execução | Início | Passaram | Falharam | Duração |
|---|---|---|---|---|
| r1 | 22/11/2026 19:54:08 | 15 | 1 (CT13) | 53,5 s |
| r2 | 22/11/2026 19:55:02 | 15 | 1 (CT13) | 50,5 s |
| r3 | 22/11/2026 19:55:53 | 15 | 1 (CT13) | 51,9 s |

O resultado foi o mesmo nas três execuções. A falha do CT13 é um defeito do sistema
(DEF-01), não instabilidade do teste: nas três vezes a venda foi aceita com total
R$ 60,00 e o estoque do caderno ficou em −1.

## 6. Defeitos encontrados

Detalhes em `projeto-anterior/registro_defeitos_stockmaster.csv`.

| ID | Severidade | Defeito | Evidência |
|---|---|---|---|
| DEF-01 | Alta | Venda com o mesmo produto em duas linhas é aceita mesmo passando do estoque; o estoque fica negativo | CT13 nas 3 execuções; `resultados/projeto-anterior/evidencias/test_ct13_mesmo_produto_em_duas_linhas.png` |
| DEF-02 | Média | `GET /vendas/{id}` de venda inexistente devolve 500 em vez de 404 | `resultados/projeto-anterior/evidencias/defeitos_api.txt` |
| DEF-03 | Baixa | Endereço inexistente devolve 500 em vez de 404 (o tratador genérico captura tudo) | `resultados/projeto-anterior/evidencias/defeitos_api.txt` |
| DEF-04 | Alta | O projeto não compilava: `ProdutoEstoqueCriticoDTO.java` continha uma cópia de `ProdutoRequestDTO` | log do Maven; corrigido para poder testar |
| DEF-05 | Alta | Vendas simultâneas perdem baixas de estoque (atualização perdida). Achado no teste de desempenho | linhas `[CONSISTENCIA]` dos logs em `resultados/projeto-anterior/` do repositório do Trabalho 1 |

## 7. Dificuldades e limitações

- **Os testes passam por uma camada web criada para o trabalho.** Ela foi mantida sem regra nenhuma, justamente para não mascarar o comportamento da API.
- **Algumas mensagens de validação vêm do Bean Validation e dependem do idioma da JVM.** É o caso de "deve ser maior que ou igual a 0.01". Nesses casos, CT03a e CT04a conferem só o campo apontado (`preco:`, `quantidade:`), não o texto exato.
- **Não foram cobertos** entradas e saídas avulsas de estoque (`/movimentacoes`), edição e exclusão de produto, nem os relatórios. As regras de estoque e desconto foram cobertas pelo fluxo de venda.
- **A regra "nome único" foi testada só com o nome idêntico.** O sistema compara com diferença entre maiúsculas e minúsculas, e não há regra escrita dizendo se "caneta" e "Caneta" devem ser iguais, então isso não virou caso de teste.
- **A suíte deve rodar em sequência** (o banco é compartilhado), em Chrome headless.
