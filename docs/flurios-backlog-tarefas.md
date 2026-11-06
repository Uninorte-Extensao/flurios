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
| 3.7 | Endpoint `PATCH /encomendas/{id}/status` (acao de Empresa, nao de Cliente) | P0 | 🟡 | 3.3, 1.10 |
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

*Três pessoas podem dividir: uma em Embarcação (4.1–4.2), outra em Rota (4.3), outra em Parada (4.4–4.6).*

---

## MÓDULO 5 — Viagens

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| 5.1 | Model `Viagem` + migration | P0 | 🟢 | 4.1, 4.3 |
| 5.2 | Endpoint `POST /viagens` (cadastro) | P0 | 🟢 | 5.1 |
| 5.3 | Endpoint `POST /viagens/{id}/encomendas` (associar encomenda à viagem) | P0 | 🟡 | 5.1, 3.4 |
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
| 7.4 | Endpoint `POST /encomendas/{id}/retirada` (com validação de termo aceito) | P0 | 🟡 | 7.2, 6.2 |
| 7.5 | Schema de saída com CPF mascarado (nunca devolver CPF completo) | P0 | 🟡 | 7.4 |
| 7.6 | Revisão dedicada: conferir que nenhum endpoint devolve CPF sem máscara | P0 | 🟡 | 7.5 |

---

## MÓDULO 8 — Dashboard
*Só leitura — bom módulo de "preenchimento" se alguém terminar cedo.*

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| 8.1 | Endpoint `GET /dashboard/resumo` (contagens por status) | P1 | 🟢 | 3.7 |
| 8.2 | Endpoint com contagem de viagens em andamento | P1 | 🟢 | 5.4 |
| 8.3 | Endpoint com contagem por município de destino | P2 | 🟡 | 6.4 |
| 8.4 | ✅ Endpoint `GET /dashboard/ocupacao` (ocupação por viagem em andamento) — concluída | P1 | 🟡 | 5.4 |
| 8.5 | ✅ Endpoint `GET /dashboard/envios-ativos` (progresso e próxima parada) — concluída | P1 | 🟡 | 6.4 |
| 8.6 | ✅ Endpoint `GET /dashboard/movimentacoes-recentes` (com limite) — concluída | P1 | 🟢 | 6.1 |

---

## FRONTEND — Área da Empresa e Área do Cliente

| # | Tarefa | Prioridade | Dificuldade | Depende de |
|---|---|---|---|---|
| F.0 | ✅ Base do frontend: React Router, camada `services/`, contexto de autenticação, rotas protegidas por tipo e design system em CSS — concluída | P0 | 🟡 | 0.5, 1.6 |
| F.1 | Tela de login | P0 | 🟢 | 1.6 |
| F.2 | Tela de cadastro de cliente | P0 | 🟢 | 2.3 |
| F.3 | ✅ Tela de cadastro de encomenda (lado cliente): origem fixa Manaus, destino e destinatário (existente ou novo), código de rastreio com botão de copiar; menu do cliente com Início, Nova encomenda e Minhas encomendas (rota provisória até a F.4) — concluída | P0 | 🟡 | 3.4, 3.9, 4.7, 2.7 |
| F.4 | Tela "meus códigos" + rastreamento com linha do tempo | P0 | 🟡 | 6.4 |
| F.5 | Telas administrativas: embarcação, rota, viagem | P0 | 🟡 | 4.2, 4.6, 5.2 |
| F.6 | Tela de gestão de encomendas (empresa) | P0 | 🟡 | 3.6 |
| F.7 | Tela de retirada (funcionário) com termo de compromisso | P0 | 🟡 | 7.4 |
| F.8 | Tela de dashboard | P1 | 🟢 | 8.1 |

---

## MELHORIAS FUTURAS (fora do MVP)

- **Peso da encomenda** (`peso_kg`): campo opcional no cadastro, útil para calcular a ocupação da embarcação. Não faz parte do MVP.

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
