# Flurios

Plataforma de gestao e rastreamento de entregas fluviais na Amazonia (Manaus <-> municipios do interior). Projeto academico (UEA).

## Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Alembic, Pydantic, JWT, pytest. Banco SQLite por enquanto.
- **Frontend**: React (Vite).

## Backend

O backend **sempre roda a partir do ambiente virtual do projeto** (`backend/.venv`). Rodar `pytest` ou `uvicorn` fora dele vai falhar com `ModuleNotFoundError`, pois as dependencias nao estao instaladas no Python global do sistema.

### Configuracao inicial

```
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell/cmd)
# source .venv/bin/activate      # Linux/Mac
pip install -r requirements.txt
```

Copie `.env.example` para `.env` e defina ao menos `SECRET_KEY`:

```
cp .env.example .env
```

Variaveis disponiveis (todas opcionais, exceto `SECRET_KEY`):

| Variavel | Padrao | Descricao |
|---|---|---|
| `SECRET_KEY` | *(obrigatoria)* | chave usada para assinar os tokens JWT |
| `DATABASE_URL` | `sqlite:///flurios.db` | URL de conexao do banco |
| `ALGORITHM` | `HS256` | algoritmo de assinatura do JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | validade do token de acesso |

### Rodando as migrations

```
cd backend
.venv\Scripts\python -m alembic upgrade head
```

### Subindo a API

```
cd backend
.venv\Scripts\python -m uvicorn app.main:app --reload
```

A API sobe em `http://127.0.0.1:8000`. Healthcheck em `GET /health`.

### Rodando os testes

```
cd backend
.venv\Scripts\python -m pytest tests -v
```

### Dashboard

Endpoints somente leitura em `/dashboard/*`, restritos a usuarios da empresa.

**Ocupacao (`GET /dashboard/ocupacao`)**: a `capacidade` da embarcacao e tratada como **numero de encomendas** (nao peso nem volume). A ocupacao de cada viagem em andamento e `encomendas ativas associadas / capacidade` (ex.: `0.375` = 37,5%). Encomenda "ativa" e a que esta associada a viagem e **nao** esta `entregue` nem em `imprevisto`. O valor pode passar de `1.0` se houver mais encomendas que a capacidade.

**Envios ativos (`GET /dashboard/envios-ativos`)**: todas as encomendas que nao estao `entregue` (inclui `imprevisto`). Para cada uma: codigo de rastreio, destinatario, municipio de destino, proxima parada, status e progresso. O progresso e a proporcao (0 a 1) das paradas da rota ja registradas na viagem da encomenda (a mais recente nao cancelada); a proxima parada e a primeira da rota, por ordem, ainda nao registrada. Sem viagem (ou com viagem cancelada) o progresso e `0.0` e a proxima parada e `null`.

**Movimentacoes recentes (`GET /dashboard/movimentacoes-recentes?limite=`)**: ultimas movimentacoes de todas as encomendas, da mais recente para a mais antiga, com codigo de rastreio, status, parada (`null` se nao houver) e data. `limite` padrao 10, minimo 1, maximo 100 (fora disso a API responde 422).

## Frontend

```
cd frontend
npm install
npm run dev
```

A aplicacao sobe em `http://localhost:5173` e consome a API em `http://127.0.0.1:8000`.

## Documentacao

- Backlog de tarefas: `docs/flurios-backlog-tarefas.md`
- Regras de trabalho e padroes do projeto: `CLAUDE.md`
- Referencias visuais do frontend: `design/`
