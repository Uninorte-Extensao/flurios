# Flurios — Instruções para o Claude Code

Plataforma de gestão e rastreamento de entregas fluviais na Amazônia (Manaus ↔ municípios do interior). Projeto acadêmico (UEA), equipe de 7 pessoas. Objetivo desta fase: **primeira versão funcional (MVP)**, backend + frontend.

## Como trabalhar (regras fixas)

1. **Antes de codar qualquer coisa**, leia o que já existe (`backend/`, `frontend/`, `docs/`, `design/`, `README.md`, `docker-compose.yml`) e siga os padrões já usados. Não reescreva o que já funciona.
2. **Uma tarefa por vez**, na ordem do backlog (`docs/flurios-backlog-tarefas.md` — IDs 0.x, 1.x ... 8.x, F.1 ... F.8 e A.1 ... A.10 do lote de acabamento). Não pule dependências. Antes de começar uma tarefa, diga qual é e o que vai fazer em 2–3 linhas.
3. **Uma branch e um commit por tarefa.**
   - Branch a partir de `develop` (se não existir, avise o usuário antes de criar): `feature/<ID>-<slug>`, ex.: `feature/T1.3-hash-senha` ou `feature/F.8-dashboard`. Correção fora da ordem do backlog: `fix/<slug>`; manutenção e documentação: `chore/<slug>`.
   - Ao terminar: rodar os testes, commitar, `git push -u origin <branch>`, mesclar em `develop` com `git merge --no-ff` (sem tocar na `main`) e dar `git push origin develop`, para a próxima tarefa partir do código atualizado.
   - Nunca commitar direto na `main`. Nunca usar `--force`, `--no-verify` nem `reset --hard`.
   - Mensagem de commit no padrão do projeto: `tipo(escopo): descrição curta em português`, ex.: `feat(auth): T1.3 hash de senha e criar_usuario`. Tipos: `feat`, `fix`, `test`, `chore`, `docs`, `refactor`. Escopos: `auth`, `clientes`, `encomendas`, `embarcacoes`, `rotas`, `viagens`, `rastreio`, `retirada`, `dashboard`, `front`, `infra`.
   - Um commit por tarefa (pode ser mais de um só se a tarefa for grande; nunca misturar duas tarefas).
4. **Cada tarefa só termina com testes passando.** Antes do commit e do merge em `develop`, rodar e ver passar: `pytest` (backend) e `npm run lint`, `npm test` e `npm run build` (frontend). Se algo falhar, corrija antes do commit. Se travar, pare e explique em vez de improvisar.
   - **Rode os testes em um comando próprio e confira o código de saída antes de commitar.** Nunca encadeie `pytest ... | tail` (nem qualquer pipe) com `&& git commit`: o pipe devolve o código de saída do último comando (`tail`), então um teste que falhou não impede o commit. Para enxugar a saída use `-q`, ou grave em arquivo e leia o código: `python -m pytest -q > saida.txt; echo "pytest=$?"`.
5. **Não invente requisitos.** Se algo estiver ambíguo ou conflitar com as regras abaixo, pergunte.
6. Ao fim de cada tarefa, responda em poucas linhas: o que foi feito, arquivos principais, como testar, próxima tarefa sugerida.

## Stack

- **Backend** (`backend/`): Python, FastAPI, SQLAlchemy, Alembic, Pydantic, JWT, bcrypt/passlib, pytest. **Banco: SQLite por enquanto** (simples e rápido); escreva código sem depender de recursos exclusivos do PostgreSQL para permitir a troca depois.
- **Frontend** (`frontend/`): React (Vite), componentes reutilizáveis, chamadas à API em uma camada `services/`. Enquanto uma rota do backend não existir, use dados simulados isolados em um único lugar, fáceis de trocar pela API real.
- Padrão de cada módulo do backend: `model → schema → service → router → test`.

## Regras de negócio (decisões já tomadas — não mudar)

- Só existem **dois tipos de cadastro/conta**: **Cliente** (quem envia a encomenda, tem login) e **Empresa** (usuários internos: Administrador, Atendente, Operador de embarcação, Funcionário do ponto de retirada). **Destinatário não tem login**, é só um cadastro de dados.
- Toda encomenda tem **um único destino**. Encomenda para cidades diferentes vira encomendas separadas, cada uma com seu código de rastreio. Código gerado pelo sistema, único.
- Rastreio exige **login**; um cliente logado vê vários códigos (os dele). Sem dado extra além do código. Só quem cadastrou recebe o código.
- Status da encomenda: `pendente → recebida → aguardando_embarque → embarcada → em_transito → chegou_ao_destino → a_retirar → entregue`, mais `imprevisto` (ex.: viagem atrasada/cancelada). Viagem cancelada → encomendas associadas viram `imprevisto` (podem ser realocadas depois).
- **Atualização de localização é manual**, feita pelo operador ao chegar em cada parada cadastrada da rota. Sem GPS/mapa automático no MVP. Sem notificação externa (WhatsApp/SMS/e-mail): o cliente acompanha dentro do sistema.
- **Retirada**: pessoa autorizada é **obrigatória**; o CPF de quem retira é guardado completo, mas **nunca devolvido completo pela API nem exibido completo na interface** (sempre mascarado, ex.: `123.***.***-45`); exige aceite de **termo de compromisso**.
- Toda mudança de status gera uma **movimentação** no histórico automaticamente.
- LGPD: não logar CPF, senha ou token. Senhas sempre com hash.

## Frontend — identidade visual (obrigatório seguir)

Referências em `design/`: painel da transportadora (web), visão do cliente (web) e versão mobile. **Toda tela nova deve parecer parte da mesma família**: mesmo header, menu lateral, cards, tabelas, badges, tipografia e espaçamento. Para telas sem referência (login, cadastro de cliente, nova encomenda, gestão de embarcações/rotas/viagens, retirada, dashboard), derive o layout dos prints existentes.

- Header azul `#135999` (o azul principal da paleta, não o azul escuro) com logo FLURIOS (barco e ondas), busca no centro, sino de notificação, usuário logado à direita.
- Menu lateral (web): Painel Operacional, Embarcações, Rotas, Viagens, Encomendas, Dashboard; rodapé com Suporte e Sair. Item ativo em verde. No mobile: barra inferior (Início, Encomendas, Viagens, Embarcações, Rotas).
- Cards brancos com cantos arredondados e sombra leve sobre fundo azul-gelo; KPIs com número grande; tabelas com cabeçalho cinza claro; barras de progresso azul/verde.
- Paleta (extraída dos protótipos): azul principal `#135999`, azul escuro `#0A2F52`, verde `#53BD92` / escuro `#3A9975`, fundo gelo `#EAF3FB`, cartão `#F6F9FC`, texto `#1F2937`, cinza `#64748B`, âmbar `#D99A3D`, coral `#E0706E`.
- Badges de status: Em trânsito (azul claro), Pendente (amarelo), Entregue (verde), Imprevisto (vermelho), Embarcada (azul claro).
- Fontes: Arial/sem serifa limpa. Português do Brasil em toda a interface. Responsivo (web e mobile).
- Visão do cliente: linha do tempo horizontal com paradas (Manaus → … → destino), balão "Em trânsito" sobre a embarcação, cards laterais: Detalhes da Embarcação, Rastreamento Atual (próxima parada + previsão), Retirada (pessoa autorizada).
- Visão da transportadora: KPIs (viagens em andamento, encomendas registradas, ocupação da embarcação), mapa de rastreamento em tempo real (pode ser ilustrativo/estático no MVP), tabela de envios ativos.

## Ordem de execução

Fase 0 (base) → Módulo 1 (auth) → Módulos 2 e 4 + F.1 em paralelo → Módulo 3 → Módulo 5 + F.2/F.3 → Módulo 6 → Módulo 7 + F.4/F.5/F.6 → Módulo 8 + F.7/F.8 → integração e estabilização. Primeiro verificar quais tarefas já estão feitas no repositório e **marcar como concluídas sem refazer**.
