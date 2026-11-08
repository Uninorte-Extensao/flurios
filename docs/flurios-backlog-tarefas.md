# Flurios — Backlog de Tarefas e Ordem de Execução

Cada módulo foi quebrado em tarefas pequenas o suficiente para virar uma Issue e uma branch própria — várias pessoas podem pegar tarefas do **mesmo módulo** ao mesmo tempo, desde que peguem tarefas diferentes da lista.

**Como ler cada tarefa:**
`[Prioridade] [Dificuldade] Título — depende de: ...`

Prioridade: **P0** crítico · **P1** importante · **P2** secundário · **P3** futuro
Dificuldade: 🟢 fácil · 🟡 médio · 🔴 difícil

---

## FASE 0 — Base do projeto (antes de qualquer módulo)

Ninguém consegue trabalhar em módulos sem isso pronto primeiro. Poucas tarefas, mas travam tudo — priorize concluir no dia 1.

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| 0.1 | Criar repositório, branches `main`/`develop`, `.gitignore`, README | P0 | 🟢 | — |
| 0.2 | Subir esqueleto do FastAPI (`main.py`) com rota `/health` | P0 | 🟢 | 0.1 |
| 0.3 | Configurar conexão com banco (`db/base.py`, `db/session.py`) | P0 | 🟡 | 0.2 |
| 0.4 | Inicializar Alembic (migrations) | P0 | 🟡 | 0.3 |
| 0.5 | Subir esqueleto do frontend (React) com tela de teste chamando `/health` | P0 | 🟢 | 0.2 |
| 0.6 | Configurar CI (GitHub Actions rodando testes em cada PR) | P1 | 🟡 | 0.1 |

**Só depois da Fase 0 concluída os módulos abaixo começam.**

---

## MÓDULO 1 — Autenticação & Usuários
*Trava os outros módulos — priorizar no início.*

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| 1.1 | Criar model `Usuario` + migration | P0 | 🟢 | Fase 0 |
| 1.2 | Criar schemas `UsuarioCreate` / `UsuarioOut` / `LoginRequest` | P0 | 🟢 | 1.1 |
| 1.3 | Implementar hash de senha e função `criar_usuario` (service) | P0 | 🟡 | 1.2 |
| 1.4 | Implementar geração de JWT e função `autenticar` (service) | P0 | 🟡 | 1.3 |
| 1.5 | Criar endpoint `POST /usuarios` (cadastro) | P0 | 🟢 | 1.3 |
| 1.6 | Criar endpoint `POST /usuarios/login` | P0 | 🟢 | 1.4 |
| 1.7 | Criar dependência `usuario_logado` (protege rotas de outros módulos) | P0 | 🟡 | 1.6 |
| 1.8 | Escrever testes automatizados de cadastro/login | P1 | 🟢 | 1.6 |
| 1.9 | Criar model `Empresa` (vinculado a `Usuario`, com `perfil`: administrador/atendente/operador_embarcacao/funcionario_retirada) + migration | P0 | 🟢 | 1.1 |
| 1.10 | Criar schemas `EmpresaCreate`/`EmpresaOut`, service de cadastro de empresa e dependência `empresa_logado` (impede que um `Usuario` seja Cliente e Empresa ao mesmo tempo) | P0 | 🟡 | 1.9 |
| 1.11 | Endpoint `POST /empresas` (só administrador cria novos usuários de empresa) + script de linha de comando para criar o primeiro administrador | P0 | 🟡 | 1.10 |

*Até 2 pessoas em paralelo: uma em 1.1–1.4 (modelagem/lógica), outra em 1.5–1.8 (endpoints/testes) assim que os schemas (1.2) estiverem prontos.*

---

## MÓDULO 2 — Clientes & Destinatários

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| 2.1 | Criar model `Cliente` (vinculado a `Usuario`) + migration | P0 | 🟢 | 1.1 |
| 2.2 | Criar model `Destinatario` (sem login) + migration | P0 | 🟢 | Fase 0 |
| 2.3 | Endpoint `POST /clientes` (completa CPF/telefone após cadastro do usuário) | P0 | 🟢 | 2.1, 1.5 |
| 2.4 | Endpoint `POST /destinatarios` | P0 | 🟢 | 2.2 |
| 2.5 | Endpoint `GET /destinatarios/{id}` | P1 | 🟢 | 2.4 |
| 2.6 | Validação de CPF (formato) nos dois cadastros | P1 | 🟡 | 2.3, 2.4 |
| 2.7 | ✅ Endpoint `GET /destinatarios` (lista do cliente logado, CPF mascarado) | P0 | 🟢 | 2.4 |

*Pode dividir em 2 pessoas: uma cuida de Cliente (2.1, 2.3), outra de Destinatário (2.2, 2.4, 2.5) — juntam-se na 2.6.*

---

## MÓDULO 3 — Encomendas
*O módulo mais importante do sistema — não deixar para o fim.*

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| 3.1 | Criar model `Encomenda` + migration | P0 | 🟡 | 2.1, 2.2 |
| 3.2 | Implementar geração de código de rastreio único | P0 | 🟡 | 3.1 |
| 3.3 | Definir e validar lista fixa de status | P0 | 🟢 | 3.1 |
| 3.4 | Endpoint `POST /encomendas` (cadastro) | P0 | 🟡 | 3.2, 3.3 |
| 3.5 | Endpoint `GET /encomendas/{codigo}` | P0 | 🟢 | 3.4 |
| 3.6 | Endpoint `GET /encomendas?cliente_id=` (lista do cliente) | P1 | 🟢 | 3.4 |
| 3.7 | Endpoint `PATCH /encomendas/{id}/status` (acao de Empresa, nao de Cliente; **`entregue` nao e aceito aqui, so a retirada gera: 422 — A.5; e quem ja esta `entregue` nao muda mais: 409 — B.3**) | P0 | 🟡 | 3.3, 1.10 |
| 3.8 | Testes automatizados (cadastro, geração de código, mudança de status) | P1 | 🟡 | 3.7 |
| 3.9 | ✅ Destino na encomenda: `parada_destino_id` (nullable na migration, obrigatório em `POST /encomendas`, não pode ser a parada de ordem 1/origem); `EncomendaOut` devolve `destino_nome` | P0 | 🟡 | 3.4, 4.6 |

*Duas pessoas em paralelo: uma em modelagem + geração de código (3.1–3.3), outra em endpoints (3.4–3.8) assim que 3.1 estiver pronto.*

---

## MÓDULO 4 — Embarcações, Rotas e Paradas
*Bom módulo para quem está começando com FastAPI — sem regra de negócio complexa.*

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| 4.1 | Model `Embarcacao` + migration | P0 | 🟢 | Fase 0 |
| 4.2 | CRUD de embarcação (endpoints) | P0 | 🟢 | 4.1 |
| 4.3 | Model `Rota` + migration | P0 | 🟢 | Fase 0 |
| 4.4 | Model `Parada` (com campo `ordem`) + migration | P0 | 🟢 | 4.3 |
| 4.5 | Validar que `ordem` não se repete na mesma rota | P1 | 🟡 | 4.4 |
| 4.6 | CRUD de rota + paradas (endpoints) | P0 | 🟡 | 4.4 |
| 4.7 | ✅ Endpoint `GET /rotas/destinos` (paradas de todas as rotas, exceto a de ordem 1; qualquer usuário logado) | P0 | 🟢 | 4.6 |
| 4.8 | ✅ Endpoint `GET /empresa/encomendas` (só empresa; não colide com `GET /encomendas`, do cliente): filtros opcionais `status` (repetível), `parada_destino_id`, `rota_id` (destino pertence à rota), `sem_viagem_ativa` e `busca` por código (parcial); paginação `limite` (1–100, padrão 20) e `deslocamento`; resposta `{itens, total, limite, deslocamento}`, cada item com código, status, descrição, destinatário (nome e CPF mascarado), destino, data e `viagem_ativa` — concluída | P0 | 🟢 | 3.6, 5.3 |

*Três pessoas podem dividir: uma em Embarcação (4.1–4.2), outra em Rota (4.3), outra em Parada (4.4–4.6).*

---

## MÓDULO 5 — Viagens

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| 5.1 | Model `Viagem` + migration | P0 | 🟢 | 4.1, 4.3 |
| 5.2 | Endpoint `POST /viagens` (cadastro) | P0 | 🟢 | 5.1 |
| 5.3 | Endpoint `POST /viagens/{id}/encomendas` (associar encomenda à viagem; **leva a encomenda a `aguardando_embarque`, com movimentação — A.2**) | P0 | 🟡 | 5.1, 3.4 |
| 5.4 | Endpoint `PATCH /viagens/{id}/status` | P0 | 🟢 | 5.1 |
| 5.5 | Regra de cancelamento (encomendas associadas viram "imprevisto") | P0 | 🟡 | 5.4, 3.7 |
| 5.6 | Listagem de viagens com filtro por status | P1 | 🟢 | 5.2 |

---

## MÓDULO 6 — Rastreamento & Movimentação

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| 6.1 | Model `Movimentacao` + migration | P0 | 🟢 | 3.1 |
| 6.2 | Conectar mudança de status da encomenda à criação automática de movimentação | P0 | 🔴 | 6.1, 3.7 |
| 6.3 | Endpoint de registro manual de localização pelo operador | P0 | 🟡 | 6.1, 5.1 |
| 6.4 | Endpoint `GET /encomendas/{codigo}/rastreio` (histórico completo, exige login) | P0 | 🟡 | 6.1, 1.7 |
| 6.5 | Testes automatizados da linha do tempo | P1 | 🟡 | 6.4 |

*A tarefa 6.2 é a mais delicada do módulo (conecta dois módulos) — recomendo que fique com quem já fez o Módulo 3, para não duplicar entendimento da máquina de status.*

---

## MÓDULO 7 — Retirada & Pessoa Autorizada
*Parte mais sensível do sistema (dado pessoal) — revisar com atenção redobrada.*

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| 7.1 | Model `PessoaAutorizada` + migration | P0 | 🟢 | 3.1 |
| 7.2 | Model `Retirada` + migration | P0 | 🟢 | 3.1 |
| 7.3 | Endpoint `POST /encomendas/{id}/pessoa-autorizada` (obrigatório) | P0 | 🟡 | 7.1 |
| 7.4 | Endpoint `POST /encomendas/{id}/retirada` (com validação de termo aceito; **só `funcionario_retirada` e `administrador`, 403 para os demais — A.1**) | P0 | 🟡 | 7.2, 6.2 |
| 7.5 | Schema de saída com CPF mascarado (nunca devolver CPF completo) | P0 | 🟡 | 7.4 |
| 7.6 | Revisão dedicada: conferir que nenhum endpoint devolve CPF sem máscara | P0 | 🟡 | 7.5 |

---

## MÓDULO 8 — Dashboard
*Só leitura — bom módulo de "preenchimento" se alguém terminar cedo.*

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| 8.1 | Endpoint `GET /dashboard/resumo` (contagens por status) | P1 | 🟢 | 3.7 |
| 8.2 | Endpoint com contagem de viagens em andamento | P1 | 🟢 | 5.4 |
| 8.3 | Endpoint com contagem por município de destino (**agrupa pelo destino real da encomenda, `parada_destino_id` — A.4**) | P2 | 🟡 | 6.4 |
| 8.4 | ✅ Endpoint `GET /dashboard/ocupacao` (ocupação por viagem em andamento) — concluída | P1 | 🟡 | 5.4 |
| 8.5 | ✅ Endpoint `GET /dashboard/envios-ativos` (progresso e próxima parada; `municipio_destino` pelo destino real da encomenda — B.2) — concluída | P1 | 🟡 | 6.4 |
| 8.6 | ✅ Endpoint `GET /dashboard/movimentacoes-recentes` (com limite) — concluída | P1 | 🟢 | 6.1 |

---

## FRONTEND — Área da Empresa e Área do Cliente

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| F.0 | ✅ Base do frontend: React Router, camada `services/`, contexto de autenticação, rotas protegidas por tipo e design system em CSS — concluída | P0 | 🟡 | 0.5, 1.6 |
| F.1 | Tela de login | P0 | 🟢 | 1.6 |
| F.2 | Tela de cadastro de cliente | P0 | 🟢 | 2.3 |
| F.3 | ✅ Tela de cadastro de encomenda (lado cliente): origem fixa Manaus, destino e destinatário (existente ou novo), código de rastreio com botão de copiar; menu do cliente com Início, Nova encomenda e Minhas encomendas (rota provisória até a F.4) — concluída | P0 | 🟡 | 3.4, 3.9, 4.7, 2.7 |
| F.4 | ✅ Tela "meus códigos" + rastreamento com linha do tempo (cliente): lista de encomendas (tabela no desktop, cards no mobile), detalhe com linha do tempo da mais recente para a mais antiga, tela "Encomenda não encontrada", busca do header ligada ao detalhe e pessoa autorizada (CPF mascarado) com cadastro/troca — concluída | P0 | 🟡 | 6.4, 7.3 |
| F.5 | Telas administrativas: embarcação, rota, viagem — dividida em F.5a (embarcações e rotas) e F.5b (viagens) | P0 | 🟡 | 4.2, 4.6, 5.2 |
| F.5a | ✅ Telas da empresa para embarcações (`/empresa/embarcacoes`) e rotas (`/empresa/rotas`, com detalhe e paradas em `/empresa/rotas/:id`): lista (tabela no desktop, cards no mobile), cadastro e edição de embarcação, cadastro de rota, adicionar/remover paradas com aviso de que a ordem 1 deve ser Manaus; criar e editar só para administrador, demais perfis em modo leitura (regra só na interface) — concluída | P0 | 🟡 | 4.2, 4.6, F.0 |
| F.5b | ✅ Telas de viagens da empresa (`/empresa/viagens` e `/empresa/viagens/:id`): lista com filtro por status, programar viagem (embarcação ativa, rota e saída no horário de Manaus), detalhe com paradas da rota, iniciar/concluir/cancelar (cancelamento com confirmação avisando que as encomendas viram imprevisto; 409 com mensagem em português), registro manual de localização (só em andamento) e lista das encomendas da viagem com ocupação — concluída. Associar e desassociar encomendas pela tela ficaram para a F.6 (concluída). Todos os perfis da empresa podem escrever em viagens (o backend não restringe por perfil) | P0 | 🟡 | 5.2, 5.4, 5.5, 5.6, F.5a |
| F.6 | ✅ Gestão de encomendas pela empresa (`/empresa/encomendas` e `/empresa/encomendas/:codigo`), usando `GET /empresa/encomendas` (4.8): lista com busca por código, filtros de status, destino e "somente sem viagem ativa", paginação de 10 em 10, tabela no desktop e cards no mobile, estados vazio, carregando e erro; detalhe com dados (CPF mascarado), linha do tempo, mudança de status com aviso de que gera movimentação, associar à viagem (viagens programadas ou em andamento cuja rota contém o destino; só encomendas recebida ou aguardando embarque) e realocar (imprevisto -> recebida -> abre a associação); na tela da viagem, associar encomendas elegíveis e remover com a viagem programada (`DELETE /viagens/{id}/encomendas/{encomenda_id}`); 409 do backend em português (`mensagens.js`) — concluída. Prints em `docs/prints-teste/` | P0 | 🟡 | 3.6, 4.8, F.5b |
| F.7 | ✅ Retirada da encomenda no destino: fila em `/empresa/retiradas` (`GET /empresa/encomendas?status=a_retirar`, busca por código, estados vazio/carregando/erro, tabela no desktop e cards no mobile) e tela `/empresa/retiradas/:codigo` com dados, destinatário e pessoa autorizada (CPF sempre mascarado), CPF de quem retira com máscara de digitação (só no estado do formulário: nunca em URL, localStorage, log ou mensagem de erro), termo de compromisso com aceite e `POST /encomendas/{id}/retirada`; sucesso volta à fila com a confirmação (código, data e hora); 403 (CPF diferente) e 409 com mensagem em português sem revelar o CPF correto; termo não aceito e CPF inválido são barrados antes de enviar. Tela e item de menu só para `funcionario_retirada` e `administrador` — **a regra de perfil também vale no backend** (A.1: 403 para os demais perfis da empresa) — concluída. Prints em `docs/prints-teste/` (15 a 24) | P0 | 🟡 | 7.4 |
| F.8 | ✅ Dashboard da empresa, somente leitura, para qualquer perfil da empresa: é a página inicial `/empresa` (título "Painel Operacional", no lugar do placeholder) e também `/empresa/dashboard` (item "Dashboard" do menu lateral; a barra inferior mobile não repete o item, pois "Início" já abre o mesmo painel — A.6). Um bloco por endpoint de `/dashboard/*`, cada um com carregando, vazio e erro próprios (falha de um não derruba os outros): cards de resumo (total e um por status, `/resumo`), viagens por status (`/viagens`), ocupação das embarcações em barra de progresso com nº de encomendas como capacidade (`/ocupacao`), encomendas por município em barras horizontais (`/municipios`, pelo destino real da encomenda; encomendas antigas sem destino aparecem como "Sem destino definido", sempre por último — A.4), envios ativos com link para `/empresa/encomendas/:codigo` (`/envios-ativos`; tabela no desktop, cards no mobile) e movimentações recentes com data e hora de Manaus (`/movimentacoes-recentes?limite=10`); botão "Atualizar". Barras em CSS puro, sem dependência nova. Prints em `docs/prints-teste/` (25 a 30). **Regras só na tela:** envios ativos mostram 10 por vez ("Mostrar mais"), movimentações pedem 10, barra de ocupação trava em 100% (texto mostra o valor real e avisa "acima da capacidade"), progresso fica verde só em 100%, status na ordem do fluxo (imprevisto por último). Mapa de rastreamento dos protótipos ficou fora do escopo | P1 | 🟢 | 8.1 |

---

## ACABAMENTO DA PRIMEIRA VERSÃO (lote de fechamento do MVP)
*Ajustes pós-F.8, cada um em branch própria (`fix/...`) e um commit, mesclados em `develop` só com `pytest`, `npm run lint`, `npm test` e `npm run build` passando. Backend: 400 → 431 testes; frontend: 87 → 105.*

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| A.1 | ✅ Retirada restrita por perfil (`fix/retirada-restrita-por-perfil`): `POST /encomendas/{id}/retirada` só para `funcionario_retirada` e `administrador`; `atendente` e `operador_embarcacao` recebem 403 e nada é gravado. Dependência `empresa_retirada` em `core/deps.py`; `test_qualquer_perfil_da_empresa_registra_retirada` virou teste dos dois perfis permitidos + 403 para os outros; fixture `headers_funcionario_retirada` | P0 | 🟢 | 7.4, F.7 |
| A.2 | ✅ Associar leva a `aguardando_embarque` (`fix/associar-aguardando-embarque`): `POST /viagens/{id}/encomendas` grava vínculo, status e movimentação (com a viagem) no mesmo commit; encomenda que já estava aguardando não gera movimentação repetida. Desassociar já devolvia a `recebida` (feito antes; só ganhou um teste do ciclo completo). Fixture `associar_a_viagem` descarta a movimentação extra para não alterar os cenários de outros testes | P0 | 🟡 | 5.3, 6.2 |
| A.3 | ✅ Descrição da encomenda validada (`fix/validacao-descricao-encomenda`): `Field(min_length=1, max_length=255)` em `EncomendaCreate` (422 fora do intervalo); testes em 0, 1, 255 e 256 caracteres. Descrição só com espaços ainda passa (a regra pedida é só de tamanho) | P1 | 🟢 | 3.4 |
| A.4 | ✅ `/dashboard/municipios` pelo destino real (`fix/dashboard-municipios-por-destino-real`): agrupa por `parada_destino_id` (nome da parada; paradas de rotas diferentes com o mesmo nome contam juntas), não pelo município do destinatário. Encomendas antigas, sem destino, entram no grupo **"Sem destino definido"**, sempre por último. Não estava feito (agrupava por `Destinatario.municipio`) | P1 | 🟡 | 8.3, 3.9 |
| A.5 | ✅ `entregue` só pela retirada (`fix/bloqueia-status-entregue-manual`): `PATCH /encomendas/{id}/status` com `entregue` responde 422, de qualquer status de origem, sem alterar a encomenda nem gravar movimentação (a checagem fica no router, porque a retirada usa o mesmo serviço para gravar `entregue`). O teste de linha do tempo agora chega a `entregue` pela retirada de verdade | P0 | 🟢 | 3.7, 7.4 |
| A.6 | ✅ Barra inferior mobile (`fix/front-barra-inferior-mais`): no lugar dos 7 itens com fonte de 9px, até **4 itens fixos** + botão **"Mais"**; a ordem em `routes/menus.js` é a prioridade (já filtrada por perfil: `funcionario_retirada` e `administrador` têm Retiradas entre os fixos). O "Mais" abre as demais opções **e Suporte e Sair** (no mobile o menu lateral some e não havia outro caminho): fecha com Esc, toque fora e ao navegar, e fica ativo quando a tela atual é um dos itens dele. Item "Dashboard" removido da barra (Início já abre o painel). Lógica em `utils/navegacao.js`. Prints 31 e 32 | P1 | 🟡 | F.0, F.8 |
| A.7 | ✅ Busca do header da empresa (`fix/front-busca-header-empresa`): o código digitado (normalizado em maiúsculas) abre `/empresa/encomendas/:codigo`; busca vazia não navega; código inexistente cai na tela "Encomenda não encontrada". `caminhoDaBusca(area, texto)` em `utils/navegacao.js`, também usada pelo cliente. O placeholder da empresa passou de "Buscar carga, viagem..." para "Buscar encomenda pelo código...", pois só código é buscado. Print 33 | P1 | 🟢 | F.6 |
| A.8 | ✅ Modal de associar viagem sem texto cortado (`fix/front-select-viagens-texto-cortado`): o `<select>` nativo não quebra linha e cortava em "Viagem #1 · Comandante Rodrigues de"; virou uma lista de opções (radio), um cartão por viagem com status, embarcação, rota e saída, quebrando linha. Prints 34 (antes) e 35 (depois) | P1 | 🟢 | F.6 |
| A.9 | ✅ Senha mínima no backend (`fix/senha-minima-no-backend`): a regra de 6 caracteres existia só no formulário (`SENHA_MINIMA` em `CadastroCliente.jsx`) e a API aceitava 1 caractere. **Escolha: mover para o backend** — `UsuarioCreate` valida (422, mensagem em português, a senha não volta na resposta). O login **não** valida tamanho, para não barrar contas criadas antes. O aviso do formulário ficou como espelho (resposta imediata), com comentário apontando o backend | P1 | 🟢 | 1.5 |
| A.10 | ✅ Saudação com nome capitalizado (`fix/front-saudacao-nome-capitalizado`): "Olá, kaue souza" → "Olá, Kaue Souza" (preposições da/de/dos/e em minúscula, acentos, hífen e apóstrofo tratados; só apresentação, o cadastro não muda). `utils/nome.js` | P2 | 🟢 | F.4 |

**Pontos em aberto do lote 1** (situação após o lote 2):
- ✅ `/dashboard/envios-ativos` com `municipio_destino` do destinatário → resolvido em B.2.
- ✅ Cliente no mobile sem Suporte e Sair → resolvido em B.1.
- ✅ Nome do usuário no header sem capitalizar → resolvido em B.4.
- ✅ `PATCH` aceitava sair de `entregue` → resolvido em B.3.
- ✅ Select do modal de programar viagem → resolvido em B.5.
- ✅ Menu lateral (web) com "Painel Operacional" e "Dashboard" apontando para a mesma tela → resolvido em C.3 (item único; `/empresa/dashboard` redireciona).

---

## ACABAMENTO DA PRIMEIRA VERSÃO — LOTE 2
*Mesmas regras do lote 1: branch `fix/...` e um commit por item, merge em `develop` só com `pytest`, `npm run lint`, `npm test` e `npm run build` passando, cada um em comando próprio. Backend: 431 → 445 testes; frontend: 105 → 107 (testes novos do `barraTemMais` em `utils/navegacao.test.js`).*

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| B.1 | ✅ Cliente no mobile com "Mais" (`fix/front-cliente-mobile-mais`): a barra do cliente (Início, Nova encomenda, Minhas encomendas) ganhou o botão "Mais", que abre **Suporte e Sair**; antes o cliente não tinha como sair nem pedir suporte no celular. O "Mais" agora existe em toda área (`barraTemMais` em `utils/navegacao.js`): na empresa abre também os itens que não couberam, no cliente só Suporte e Sair (sem divisor). Print 36 | P1 | 🟢 | A.6 |
| B.2 | ✅ `envios-ativos` pelo destino real (`fix/dashboard-envios-ativos-destino-real`): `municipio_destino` vem de `parada_destino_id` (nome da parada), não do município do destinatário; sem destino, "Sem destino definido" (constante `MUNICIPIO_SEM_DESTINO`, a mesma do bloco de municípios, e teste garante que os dois blocos contam igual). O frontend não mudou: já exibia o campo | P1 | 🟡 | A.4, 8.5 |
| B.3 | ✅ Nada muda a partir de `entregue` (`fix/bloqueia-mudanca-a-partir-de-entregue`): `PATCH /encomendas/{id}/status` em encomenda entregue responde **409** "Encomenda ja entregue: nao e possivel alterar o status." (qualquer perfil da empresa, qualquer novo status; sem alterar nada nem gravar movimentação), com a mensagem traduzida em `mensagens.js`. A ordem das checagens é: `entregue` como destino → 422 (A.5), encomenda inexistente → 404, encomenda já entregue → 409 | P0 | 🟢 | A.5 |
| B.4 | ✅ Nome capitalizado no header (`fix/front-header-nome-capitalizado`): `capitalizarNome` (a mesma função da saudação) aplicada no `AppLayout`: "Cliente: Kaue Souza". Vale para cliente e empresa; só apresentação | P2 | 🟢 | A.10 |
| B.5 | ✅ Selects do modal de programar viagem (`fix/front-selects-programar-viagem`): **havia texto cortado** (medido no navegador: no celular, embarcação "Comandante Rodrigues de Albuquerque III (capacidade 50)" e rota "Manaus - Itacoatiara - Parintins (linha expressa via Rio Amazonas)"; no desktop, a rota). Como o `<select>` nativo não quebra linha, o texto completo da opção escolhida aparece embaixo do campo (via `ajuda` do `CampoSelecao`), e todo select fechado ganha reticências (`text-overflow: ellipsis` em `base.css`). Prints 37 (antes) e 38 (depois) | P1 | 🟢 | A.8, F.5b |

**Pontos em aberto do lote 2:**
- O select de destinatário da "Nova encomenda" (cliente) também corta no celular a 360px ("Joao Pereira · Parintins · CPF 222.***.***-05": ~275px de texto para ~230px de espaço); hoje só ganhou as reticências. Os demais selects (filtros de Encomendas e Viagens, parada em Detalhe da viagem, status em Detalhe da encomenda) não foram medidos.

---

## ACABAMENTO DA PRIMEIRA VERSÃO — LOTE 3 (correções da bateria e2e)
*Origem: `docs/relatorio-testes-e2e.md` (17 defeitos). Mesmas regras: uma branch `fix/...` por correção, um commit por item, merge em `develop` só com `pytest`, `npm run lint`, `npm test`, `npm run build` e `npm run test:e2e` passando, cada um em comando próprio. Backend: 445 (+2 xfail) → 516 testes, sem xfail; frontend: 107 → 117 testes unitários; e2e de tela: 13 cenários.*

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| C.1 | ✅ F-1 — transições de status da encomenda (`fix/transicoes-status-encomenda`): `PATCH /encomendas/{id}/status` só aceita `pendente→recebida→aguardando_embarque→embarcada→em_transito→chegou_ao_destino→a_retirar`, qualquer status (menos `entregue`) → `imprevisto`, e `imprevisto→recebida`; as demais respondem **409** ("Transicao de status invalida: a -> b."), inclusive repetir o status atual (antes era 200 sem efeito). Tabela `TRANSICOES_MANUAIS` em `services/encomenda.py`, só no PATCH: associar, desassociar, localização, cancelamento de viagem e retirada chamam o serviço direto e seguem iguais. Mensagem traduzida em `mensagens.js`. Matriz de testes com todos os pares; xfail do F-1 convertido | P0 | 🟡 | 3.7, A.5, B.3 |
| C.2 | ✅ D-1 — próxima parada e progresso dos envios ativos (`fix/dashboard-proxima-parada-progresso`): o trecho da encomenda vai da primeira parada da rota até o **destino dela**; a posição é a **última localização registrada** para a encomenda na viagem. Progresso = posição / paradas do trecho; chegou ao destino (ou `chegou_ao_destino` / `a_retirar`) = 100% e sem próxima parada. Destino fora da rota ou ausente: rota inteira (como antes). Só o `/dashboard/envios-ativos` tinha esse cálculo. xfail do D-1 convertido | P1 | 🟡 | 8.5, B.2 |
| C.3 | ✅ F-5 — um único item de menu para o painel (`fix/menu-painel-unico`): menu lateral só com "Painel Operacional" (a barra mobile já tinha só "Início"); `/empresa/dashboard` redireciona para `/empresa`. Teste do menu e e2e do redirecionamento | P1 | 🟢 | F.8, A.6 |
| C.4 | ✅ T-1 e T-3 — textos (`fix/front-textos-t1-t3`): "Viagens concluída: 1 de 3" no texto acessível das barras (`rotuloDoStatus`, em `utils/status.js`, também usado pelo `StatusBadge`); exemplo de busca `FLX5MBAFUSZ3L` (formato real: `FLX` + 10 caracteres, sem hífen) | P2 | 🟢 | F.6, F.7, F.8 |
| C.5 | ✅ F-6 — CORS (`fix/cors-127-0-0-1`): `http://127.0.0.1:5173` liberado, com teste; origem desconhecida segue bloqueada | P2 | 🟢 | 0.x |
| C.6 | ✅ V-5 — 360px (`fix/front-barra-inferior-cabecalho-360`): rótulos da barra inferior quebram em duas linhas; nome do usuário no cabeçalho em uma linha só, com reticências | P2 | 🟢 | A.6, B.4 |
| C.7 | ✅ D-2 — "Sem viagem" no lugar do traço (`fix/front-sem-viagem-marcador`): coluna Viagem da lista de encomendas; próxima parada do envio ativo ("Sem viagem" ou "No destino") | P2 | 🟢 | F.6, F.8 |
| C.8 | ✅ D-3 — "Ainda não saiu" (`fix/front-envio-ainda-nao-saiu`): envio sem viagem não mostra mais a barra em 0% | P2 | 🟢 | C.7 |
| C.9 | 🟡 V-1 (parcial) — próxima parada para o cliente (`fix/front-cliente-proxima-parada`): o card "Rastreamento atual" mostra "Próxima parada", calculada com `GET /rotas/destinos` (já ordenado por rota e ordem) e as localizações do histórico; some ao chegar ao destino. Depende dessa ordem, agora travada por teste de backend. Agrupa por `rota_nome`: duas rotas com o mesmo nome poderiam se misturar (o nome da rota não é único no banco). O restante do V-1 está em Melhorias futuras | P1 | 🟡 | 6.4, F.4 |

**Corrigidos no lote 3:** F-1, F-5, F-6, T-1, T-3, V-5, D-1, D-2, D-3 e parte do V-1.

**Dos 12 defeitos de gravidade baixa, ficaram de fora (6):**
- **F-2** (iniciar/concluir viagem não muda as encomendas): decisão de produto, coerente com "atualização manual". Aguarda confirmação.
- **F-3** (sem tela para criar atendente, operador e funcionário da retirada): exige tela nova.
- **F-4** (404 no console ao abrir encomenda sem pessoa autorizada): vem do endpoint; mudar exigiria alterar o contrato do backend.
- **T-2** (mensagens da API sem acento): são dezenas de mensagens e de testes que as comparam; a interface já traduz. Só afeta quem usa a API ou o Swagger.
- **V-3** (início do cliente quase vazio): depende da visão do cliente completa (V-1).
- **V-4** (texto repetido abaixo do select no modal de programar viagem): é intencional (B.5), evita o corte do nome longo.

---

## MELHORIAS FUTURAS (fora do MVP)

- **Peso da encomenda** (`peso_kg`): campo opcional no cadastro, útil para calcular a ocupação da embarcação. Não faz parte do MVP.
- **Visão do cliente como no protótipo (restante do V-1)** (`design/Screenshot_2.png`): linha do tempo horizontal com as paradas (Manaus → … → destino) e o balão "Em trânsito" sobre a embarcação; card "Detalhes da Embarcação"; previsão de chegada no "Rastreamento atual". Precisa de endpoint novo (ou de ampliar `GET /encomendas/{codigo}/rastreio`) com a rota completa, a embarcação e a previsão, hoje só acessíveis à empresa. Quando existir, a "próxima parada" do cliente deve passar a vir dele, em vez de ser deduzida de `/rotas/destinos`. Também melhora o início do cliente (V-3).
- **Painel Operacional como no protótipo (V-2)** (`design/Screenshot_1.png` e `Screenshot_3.png`): mapa de rastreamento (pode ser ilustrativo/estático), KPI grande de "Viagens em andamento" com barra e taxa de ocupação em anel.
- **Tela para criar contas da empresa (F-3)**: atendente, operador de embarcação e funcionário da retirada hoje só nascem por `POST /empresas` e pelo script `criar_admin`.
- **Mensagens da API com acento (T-2)**: reescrever os `detail` do backend e ajustar `mensagens.js` e os testes.
- **Decidir o comportamento da viagem sobre as encomendas (F-2)**: iniciar/concluir a viagem poderia atualizar o status das encomendas a bordo, ou continuar manual.
- **Erro 404 no console do detalhe do cliente (F-4)**: devolver a pessoa autorizada junto da encomenda, ou 200 vazio.

---

## ORDEM GERAL DE EXECUÇÃO (o que fazer primeiro no projeto)

```
FASE 0 — Base do projeto                    (dias 1–3, bloqueia tudo)
   ↓
MÓDULO 1 — Autenticação                     (trava todos os outros módulos)
   ↓
   ├── MÓDULO 2 — Clientes & Destinatários  ┐
   ├── MÓDULO 4 — Embarcações/Rotas/Paradas │  podem andar em paralelo
   └── F.1 — Tela de login (frontend)       ┘  assim que o Módulo 1 terminar
   ↓
MÓDULO 3 — Encomendas                       (depende de 2)
   ↓
   ├── MÓDULO 5 — Viagens                   ┐  podem andar em paralelo
   └── F.2, F.3 — Telas de cliente          ┘  assim que 3 e 4 terminarem
   ↓
MÓDULO 6 — Rastreamento & Movimentação      (depende de 3 e 5)
   ↓
   ├── MÓDULO 7 — Retirada                  ┐  podem andar em paralelo
   └── F.4, F.5, F.6 — Telas restantes      ┘  assim que 6 terminar
   ↓
MÓDULO 8 — Dashboard + F.7, F.8             (por último — só leitura, mais simples)
   ↓
INTEGRAÇÃO E ESTABILIZAÇÃO                  (reservar pelo menos 2 semanas no fim)
```

**Regra prática:** nunca deixe mais de uma pessoa parada esperando o Módulo 1 ou o Módulo 3 terminarem — enquanto isso, adiante o Módulo 4 (não depende de nada) e o setup do frontend (F.1), que também não dependem de backend pronto (dá pra usar dados simulados).
