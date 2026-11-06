# Relatório da T7.6 — Revisão: nenhum endpoint devolve CPF sem máscara

Data: 2026-11-05 · Escopo: todo o `backend/app` (36 operações da API) e `frontend/src`.

## Regra verificada

O CPF é guardado completo (11 dígitos), mas **nunca** pode sair completo pela API, nem ser exibido completo na interface, nem ir para log. Formato de saída: `123.***.***-45`.

## Como foi verificado

1. **Leitura**: busca por `cpf` em `app/` (models, schemas, services, routers), por `logging`/`print`, e por `cpf` em `frontend/src`.
2. **Varredura estática** (`tests/test_auditoria_cpf.py`): percorre o `response_model` de toda rota, inclusive modelos aninhados, e lista campos de CPF que não usam `CpfMascarado`. Um teste confere que a enumeração cobre todas as operações do OpenAPI.
3. **Varredura dinâmica** (mesmo arquivo): executa o fluxo real (cliente, destinatário, encomenda, pessoa autorizada, status, retirada, rastreio, listagens) e procura CPF em **todos** os corpos de resposta, incluindo os de erro. Conta como CPF: valor sentinela injetado, formato `ddd.ddd.ddd-dd`, ou 11 dígitos com dígito verificador válido (telefones de 11 dígitos não geram falso positivo).

## Achados

| # | Severidade | Onde | O que acontece |
|---|---|---|---|
| 1 | **Alta** | `POST /clientes` → `ClienteOut.cpf: str` | Devolve o **CPF completo** do cliente (201). |
| 2 | **Alta** | `POST /destinatarios` → `DestinatarioOut.cpf: str` | Devolve o **CPF completo** do destinatário (201). Só o `GET /destinatarios/{id}` mascara. |
| 3 | Média (latente) | `DestinatarioDetalheOut.cpf: str` | Hoje a resposta sai mascarada porque o **router** sobrescreve o campo (`routers/destinatario.py`). O schema, sozinho, não protege: qualquer outro uso do schema vaza. |
| 4 | Baixa | Respostas 422 de `POST /destinatarios`, `POST /encomendas/{id}/pessoa-autorizada`, `POST /encomendas/{id}/retirada` | O erro padrão de validação do FastAPI repete o campo `input`, ou seja, o CPF **inválido** que o chamador digitou. Não é um CPF guardado, mas pode ser um CPF real com erro de digitação e passa por proxies e ferramentas de monitoramento. |
| 5 | Informativo | `POST /clientes` com CPF já cadastrado (400 "CPF ja cadastrado.") | Não devolve CPF, mas permite descobrir se um CPF tem cadastro (enumeração). Aceitável no MVP; não corrigido. |

Os achados 1 a 4 aparecem nos testes `test_varredura_estatica_...` e `test_varredura_dinamica_...`, que travam a lista atual: qualquer campo novo de CPF sem máscara, ou resposta nova que o exponha, quebra a suíte.

## O que está correto

- `PessoaAutorizadaOut` (`POST` e `GET /encomendas/{id}/pessoa-autorizada`) e `RetiradaOut` (`POST /encomendas/{id}/retirada`) usam `CpfMascarado`: a máscara é aplicada pelo schema, não pelo router. Entrada fora do padrão sai como `***.***.***-**`.
- `GET /destinatarios/{id}` sai mascarado (via router, ver achado 3).
- Respostas 403/409/422 da retirada e da pessoa autorizada que não vêm de validação de campo usam mensagens fixas, sem CPF.
- Nenhum outro schema de saída (encomenda, viagem, rota, embarcação, movimentação, rastreio, empresa, usuário, token) tem campo de CPF, nem modelo aninhado com CPF.
- **Logs**: o backend não usa `logging`. O único `print` é de `scripts/criar_admin.py` e não imprime CPF (só `usuario_id`). Nenhum CPF trafega em URL ou query string.
- **Token JWT**: o payload tem apenas `sub` (id do usuário) e `exp`.
- **Frontend**: ainda não há nenhuma referência a CPF em `frontend/src`. Quando as telas F.7 (retirada) chegarem, devem exibir apenas o CPF mascarado recebido da API.

## Riscos residuais (fora do escopo da correção)

- O CPF fica em texto puro no banco (decisão do projeto): quem tiver acesso ao arquivo `flurios.db` lê todos os CPFs.
- Se um log de requisições (proxy, uvicorn com corpo, APM) for ligado no futuro, ele registraria o corpo dos `POST` com CPF. Hoje nada disso existe.

## Correção

Prevista na branch `fix/mascarar-cpf-respostas`: usar `CpfMascarado` em `ClienteOut`, `DestinatarioOut` e `DestinatarioDetalheOut`, remover o mascaramento manual do router, e remover o campo `input` das respostas 422. Os testes que documentam os vazamentos (`xfail`) passam a exigir resposta limpa.
