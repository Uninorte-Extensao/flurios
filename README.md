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
