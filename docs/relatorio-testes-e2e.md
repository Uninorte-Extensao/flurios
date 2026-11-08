# Relatório da bateria de testes ponta a ponta (backend + frontend)

Branch `feature/testes-e2e`, a partir de `develop`. A bateria em si **só testa e reporta**: nenhum código da aplicação foi alterado por ela. Depois dela, os defeitos foram corrigidos (ou não) em branches próprias; a coluna **Situação** de cada tabela diz o que aconteceu com cada um.

> **Situação atual (lote 3 de correções):** 9 corrigidos (F-1, F-5, F-6, T-1, T-3, V-5, D-1, D-2, D-3), 1 parcial (V-1) e 7 não alterados (F-2, F-3, F-4, T-2, V-2, V-3, V-4). Dos 5 de gravidade média (F-1, F-5, V-1, V-2, D-1), 3 estão corrigidos (F-1, F-5, D-1), V-1 está parcial e V-2 foi para Melhorias futuras. Backend: `516 passed`, sem nenhum `xfail`. Os prints em `docs/prints-teste/e2e/` são da bateria original, **anteriores às correções**.

## Resumo

| Parte | Resultado |
|---|---|
| Backend, fluxo completo pela API (`backend/tests/test_e2e_fluxo_completo.py`) | O fluxo roda inteiro. Encontrou **2 defeitos** (F-1 e D-1); os 2 testes terminavam como `xfail`. **Ambos corrigidos: os testes agora passam** |
| Backend, suíte completa | era `445 passed, 2 xfailed`; agora `516 passed` |
| Frontend, 13 cenários Playwright pelas telas (`frontend/e2e/fluxo.spec.js`) | **13 passed**. O fluxo todo é possível pelas telas |
| Prints | 68 telas em desktop (1440×900) e celular (360×740): 136 imagens em `docs/prints-teste/e2e/` |
| `npm run lint`, `npm test`, `npm run build` | passam (`npm test`: 117 testes) |
| `flurios.db` e portas 8000/5173 | não foram tocados (o runner confere a data de modificação do `flurios.db` no fim: "intacto") |

**Resumo dos defeitos (na bateria original):** 17 no total. Nenhum é bloqueante. 5 de gravidade média, 12 baixa.

| Tipo | Quantidade | IDs |
|---|---|---|
| Funcional | 6 | F-1 a F-6 |
| Texto (acentos e tradução) | 3 | T-1 a T-3 |
| Visual (alinhamento, corte, comparação com `design/`) | 5 | V-1 a V-5 |
| Dados (valores "—", progresso e próxima parada, campos vazios) | 3 | D-1 a D-3 |

## O que passou

Backend (pela API, banco SQLite temporário criado com `alembic upgrade head`):

- Administrador cria embarcação, rota (Manaus, Tefé, Coari) e paradas. Atendente é barrado (403) ao cadastrar embarcação. Ordem de parada repetida é recusada.
- Cliente se cadastra e o `/usuarios/me` muda de "sem tipo" para `cliente`. CPF inválido é recusado. O CPF do cliente, do destinatário e da pessoa autorizada nunca volta completo (sempre `111.***.***-96`).
- Destinos oferecidos ao cliente não incluem a origem. Destino = origem é recusado (422).
- Encomenda para Tefé nasce `pendente` com código de rastreio. Pessoa autorizada cadastrada (e também a opção "o destinatário é a pessoa").
- Empresa marca como recebida, associa à viagem (`aguardando_embarque`) e inicia a viagem. Localização só é aceita com a viagem em andamento. Registra localização em Manaus e em Tefé (`embarcada` → `em_transito`). Chega a `chegou_ao_destino` e `a_retirar`.
- Retirada: operador de embarcação recebe 403, retirada sem aceite do termo recebe 422, **CPF errado recebe 403** e a encomenda segue `a_retirar`. **CPF certo (mesmo digitado com pontos) entrega**, com CPF mascarado na resposta. Retirada repetida recebe 409 e uma encomenda entregue não muda mais (409).
- Rastreio do cliente com a linha do tempo completa e em ordem: pendente, recebida, aguardando embarque, embarcada, em trânsito (Manaus), em trânsito (Tefé), chegou ao destino, a retirar, entregue. Outro cliente recebe 404, sem login recebe 401, cliente no dashboard recebe 403.
- Exceção: viagem cancelada deixa a encomenda em `imprevisto` e uma viagem cancelada não reabre. Realocação: `imprevisto` → `recebida` → nova viagem → `aguardando_embarque`, com histórico completo.
- Dashboard no fim, coerente com tudo: 2 encomendas, 1 entregue, 1 aguardando embarque, 3 viagens (1 concluída, 1 cancelada, 1 programada), Tefé = 2, envios ativos = 1, e o total de movimentações igual à soma dos históricos.

Frontend (Playwright, Chromium):

1. Login (validação, senha errada, rota protegida). 2. Administrador cria embarcação, rota e três paradas pelas telas. 3. Cliente se cadastra pela tela. 4. Nova encomenda para Tefé com novo destinatário. 5. Pessoa autorizada com CPF mascarado (o CPF completo nunca aparece no HTML). 6. Atendente recebe a encomenda, programa viagem e associa. 7. Iniciar, embarcar, localização em Manaus e Tefé, chegada. 8. Cliente acompanha. 9. Funcionário da retirada: atendente sem acesso, validação, CPF errado (mensagem de erro), CPF certo com termo. 10. Cliente vê entregue. 11. Exceção: cancelar viagem, imprevisto, realocar. 12. Concluir viagem, painel e dashboard. 13. Busca do cabeçalho, proteção de rotas nos dois sentidos, rota inexistente e "Sair".

Não foi encontrado: texto em inglês, `undefined`/`null`/`NaN` na tela, rolagem horizontal da página, texto cortado ou fora da janela em 360px, select com texto cortado, imagem quebrada ou erro de JavaScript (a checagem é automática, em todas as telas, nos dois tamanhos). Os acentos estão corretos nas telas, com a exceção de T-1.

## Defeitos

Gravidade: **média** = atrapalha o uso ou contradiz uma regra do projeto; **baixa** = acabamento, texto ou caso de borda.

### Funcional

| ID | Gravidade | Onde | Descrição e como reproduzir | Situação |
|---|---|---|---|---|
| F-1 | Média | API `PATCH /encomendas/{id}/status` | A API aceita **qualquer** mudança de status (salto ou retrocesso). Só a tela restringe ao próximo passo (`TRANSICOES_MANUAIS` em `frontend/src/utils/gestaoEncomenda.js`, e o próprio comentário diz "SÓ NA TELA"). Reproduzir: com token de empresa, `PATCH` de uma encomenda `pendente` para `a_retirar` responde 200. Consequência: dá para deixar uma encomenda pronta para retirada sem nunca ter passado por viagem. Teste: `test_regras_de_transicao_de_status_da_encomenda` (xfail F-1) | ✅ **Corrigido** (`fix/transicoes-status-encomenda`): só as transições válidas; as demais respondem 409 (`Transicao de status invalida: a -> b.`). O xfail virou teste que passa e há uma matriz de testes com todos os pares de status. Associar, desassociar, localização, cancelamento e retirada não passam pela tabela e seguem funcionando |
| F-2 | Baixa | Viagem × encomendas | Iniciar ou concluir a viagem não muda as encomendas: com a viagem "Em andamento" a encomenda segue "Aguardando embarque" (tela 34). O operador precisa embarcar, marcar "Chegou ao destino" e "A retirar" encomenda por encomenda, e registrar localização no destino também não muda o status. Dá para concluir a viagem com encomendas ainda "Em trânsito". É coerente com "atualização manual", mas confirme se é a intenção. Reproduzir: telas 34 a 39 | ⏸ **Não alterado**: é decisão de produto (atualização manual pelo operador). Aguarda confirmação |
| F-3 | Baixa | Contas da empresa | Não existe tela para criar atendente, operador ou funcionário da retirada: só `POST /empresas` e o script `criar_admin`. Os testes de tela criaram essas contas pela API. Reproduzir: procurar no menu do administrador | ⏸ **Não alterado**: exige tela e fluxo novos. Vai para Melhorias futuras |
| F-4 | Baixa | Tela de detalhe do cliente | Em fluxo normal o navegador registra erro 404 no console (`GET /encomendas/{id}/pessoa-autorizada`) toda vez que o cliente abre uma encomenda ainda sem pessoa autorizada (6 ocorrências na bateria). Funciona, mas é ruído e deixa passar erros reais | ⏸ **Não alterado**: o 404 vem do próprio endpoint; para sumir seria preciso mudar o contrato do backend (200 vazio) ou carregar a pessoa autorizada junto da encomenda |
| F-5 | Média | Menu "Painel Operacional" e "Dashboard" | As duas entradas mostram **exatamente o mesmo conteúdo** (só muda o título). Reproduzir: logar como administrador e comparar `/empresa` e `/empresa/dashboard` (prints 62 e 63) | ✅ **Corrigido** (`fix/menu-painel-unico`): um único item "Painel Operacional" no menu lateral e "Início" na barra mobile; `/empresa/dashboard` redireciona para `/empresa` |
| F-6 | Baixa | CORS no backend | O CORS libera só `http://localhost:5173`. Abrir o frontend em `127.0.0.1:5173` ou outra porta faz a API recusar. A bateria contornou com um proxy `/api` no Vite de testes | ✅ **Corrigido** (`fix/cors-127-0-0-1`): `http://127.0.0.1:5173` liberado, com teste. Outras portas continuam bloqueadas |

### Texto (acentos e tradução)

| ID | Gravidade | Onde | Descrição e como reproduzir | Situação |
|---|---|---|---|---|
| T-1 | Baixa | `frontend/src/pages/empresa/Dashboard.jsx:101` | O texto acessível das barras de viagens usa o valor técnico do status: "Viagens **concluida**: 1 de 3", "Viagens **em_andamento**: ...". Sem acento e sem tradução, o leitor de tela lê isso. Reproduzir: `/empresa`, inspecionar o `aria-label` das barras de "Viagens" | ✅ **Corrigido** (`fix/front-textos-t1-t3`): "Viagens concluída: 1 de 3", via `rotuloDoStatus` (`utils/status.js`) |
| T-2 | Baixa | Mensagens da API | Os `detail` do backend vêm sem acento ("Encomenda nao encontrada.", "E-mail ou senha invalidos."). A interface traduz por `mensagens.js` e nenhuma mensagem sem tradução apareceu nas telas testadas, mas quem usa a API ou o Swagger vê o texto cru. Reproduzir: `POST /usuarios/login` com senha errada | ⏸ **Não alterado**: são quase todas as mensagens da API e os testes que as comparam; a interface já traduz. Vai para Melhorias futuras |
| T-3 | Baixa | Exemplo no campo de busca | Os campos "Buscar por código" (Encomendas e Retiradas) mostram `Ex.: FLX-ABC123`, mas os códigos reais são `FLX` + 10 caracteres **sem hífen** (ex.: `FLX5MBAFUSZ3L`, `backend/app/core/rastreio.py`). O exemplo induz ao erro. Reproduzir: `/empresa/encomendas` | ✅ **Corrigido** (`fix/front-textos-t1-t3`): exemplo agora é `FLX5MBAFUSZ3L` |

### Visual (comparação com `design/`)

| ID | Gravidade | Onde | Descrição e como reproduzir | Situação |
|---|---|---|---|---|
| V-1 | Média | Detalhe da encomenda do cliente (`/cliente/encomendas/:codigo`, prints 40, 48, 55) | A "Visão do Cliente" não segue o protótipo (`design/Screenshot_2.png`). Falta a **linha do tempo horizontal** com as paradas (Manaus → Tefé) e o balão "Em trânsito" sobre a embarcação. Falta o card **"Detalhes da Embarcação"** (nenhum texto "Detalhes da Embarcação" existe no código). O card "Rastreamento Atual" mostra "Última parada registrada" e não **próxima parada + previsão**, como pede o projeto. A linha do tempo é vertical | 🟡 **Parcial** (`fix/front-cliente-proxima-parada`): o card "Rastreamento atual" mostra a **próxima parada** (calculada com `/rotas/destinos` e o histórico, sem endpoint novo). Linha do tempo horizontal, balão, "Detalhes da Embarcação" e previsão precisam de dados que a API do cliente não entrega: Melhorias futuras |
| V-2 | Média | Painel Operacional (`/empresa`, prints 04, 24, 62) | Em relação a `design/Screenshot_1.png` e `Screenshot_3.png`: não há mapa de rastreamento (o projeto aceita ilustrativo/estático, mas não existe nem isso). Os KPIs são só contagens por status, sem o "Viagens em andamento" grande com barra nem a taxa de ocupação em anel. O que existe é consistente com a identidade (azul `#135999`, menu verde, cards, badges) | ⏩ **Melhorias futuras** (mapa e KPIs de ocupação em anel) |
| V-3 | Baixa | Início do cliente (`/cliente`, print 14) | A tela é um cartão de boas-vindas com dois botões e o resto vazio. Mesmo com encomendas, não mostra a visão da encomenda como no protótipo | ⏸ **Não alterado**: depende da visão do cliente completa (V-1). Melhorias futuras |
| V-4 | Baixa | Modal "Programar viagem" no celular (print 29) | Abaixo de cada select repete-se o texto da opção escolhida ("Rio Negro I (capacidade 5)" duas vezes). Parece resto da correção de texto cortado: não quebra nada, mas é redundante | ⏸ **Não alterado, de propósito**: o texto repetido embaixo do select é o que evita o corte do nome longo (correção B.5). Remover reabriria o corte |
| V-5 | Baixa | Barra inferior do cliente em 360px (print 40) | Os rótulos "Nova encomenda" e "Minhas encomendas" ficam quase encostados. O nome no cabeçalho quebra em 2 ou 3 linhas ("Administrador: Admin Flurios") | ✅ **Corrigido** (`fix/front-barra-inferior-cabecalho-360`): rótulos da barra quebram em duas linhas e o nome do cabeçalho fica em uma linha, com reticências quando não cabe |

### Dados

| ID | Gravidade | Onde | Descrição e como reproduzir | Situação |
|---|---|---|---|---|
| D-1 | Média | `GET /dashboard/envios-ativos` e telas do painel (a tela mostra "Progresso: 67%", prints 41 e 42; o valor da próxima parada vem do teste de backend) | **Próxima parada e progresso incoerentes com o destino.** A conta usa a rota inteira. Uma encomenda com destino **Tefé**, já registrada em Tefé, aparece com "Próxima parada: **Coari**" e "Progresso: **67%**", e só chegaria a 100% numa parada que ela nem visita. Reproduzir: rota Manaus, Tefé, Coari; encomenda para Tefé; iniciar a viagem; registrar Manaus e Tefé; olhar o envio ativo. Teste: `test_fluxo_completo_e_caminho_de_excecao` (xfail D-1) | ✅ **Corrigido** (`fix/dashboard-proxima-parada-progresso`): progresso e próxima parada seguem o trecho da encomenda (origem até o destino dela) e a última localização registrada; ao chegar ao destino, 100% e sem próxima parada. O xfail virou teste que passa |
| D-2 | Baixa | Listas e painel da empresa (prints 24, 25, 61) | O "—" aparece como valor em "Próxima parada: —" (encomenda ainda sem viagem) e na coluna de viagem das encomendas sem viagem ativa, inclusive nas entregues. É um marcador de "sem dado" legítimo, mas ocupa a coluna sem explicar. Texto como "Sem viagem" seria mais claro | ✅ **Corrigido** (`fix/front-sem-viagem-marcador`): "Sem viagem" na coluna Viagem e "Sem viagem" / "No destino" na próxima parada |
| D-3 | Baixa | Encomenda pendente (`/empresa`, print 24) | O envio ativo de uma encomenda recém-criada aparece com barra de progresso 0% e sem próxima parada, no mesmo formato de um envio em andamento, sem distinguir "ainda não saiu" | ✅ **Corrigido** (`fix/front-envio-ainda-nao-saiu`): envio sem viagem mostra "Ainda não saiu" no lugar da barra em 0% |

Campos vazios (células ou valores em branco), `undefined`, `null` ou `NaN` visíveis: nenhum encontrado.

## Como rodar

```
cd backend
.venv\Scripts\python -m pytest -q -rx                           # suíte inteira (516 passed)
.venv\Scripts\python -m pytest tests/test_e2e_fluxo_completo.py -q -rx

cd frontend
npm install
npx playwright install chromium     # uma vez (baixa o Chromium para a pasta de cache do usuário)
npm run test:e2e                    # sobe API e frontend em portas livres, banco temporário, grava os prints
```

O `npm run test:e2e` (`frontend/e2e/rodar.mjs`) escolhe duas portas livres, cria o banco em uma pasta temporária (migrations + administrador), sobe o uvicorn e o Vite (com proxy `/api`), roda o Playwright e apaga tudo no fim. Os prints e o `achados-automaticos.json` (achados de texto, visual e dados por tela, respostas HTTP com erro e erros de console) vão para `docs/prints-teste/e2e/`.

## Limitações e observações

- Os prints são de página inteira: elementos `position: fixed` (barra inferior no celular) aparecem no meio da imagem, e a barra lateral termina em 900px. Isso é efeito do print, não defeito da tela.
- O campo de data da viagem aparece no formato americano nos prints porque o Chromium do Playwright usa o idioma do sistema; não é um defeito da aplicação.
- A busca automática de "palavra sem acento" é uma lista curta de palavras comuns: ela não substitui revisão humana. Os prints foram olhados, e os acentos conferidos, nas telas principais, não em todas.
- As contas de funcionário (atendente, funcionário da retirada) foram criadas pela API na preparação (F-3). Todo o resto do fluxo de tela foi feito pela interface.
