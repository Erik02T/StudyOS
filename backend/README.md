# StudyOS Backend

Backend com:
- Auth JWT
- CRUD Subject/Task
- Planner adaptativo (Pareto + carga cognitiva + balanceamento)
- Spaced repetition (SM-2)
- Analytics avancado e dashboard API

## Executar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Testes (pytest)

```bash
pytest -q
```

## Endpoints principais

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/request-email-verification`
- `POST /auth/verify-email`
- `POST /auth/request-password-reset`
- `POST /auth/reset-password`
- `GET|POST /organizations`
- `GET|POST|PUT|DELETE /subjects`
- `GET|POST|PUT|DELETE /tasks`
- `POST /planner/generate-plan`
- `GET /reviews/due`
- `POST /reviews/answer`
- `POST /sessions/finalize`
- `GET /analytics/summary?days=30`
- `POST /analytics/performance`
- `GET /analytics/heatmap?days=30`
- `GET /analytics/dashboard?days=30`
- `GET /internal/email-queue/stats`
- `POST /internal/email-queue/process`

Todos os endpoints acima tambem estao disponiveis com prefixo versionado:
- `/v1/...`

## Multi-tenant (foundation)

- Registro de usuario cria automaticamente uma organizacao pessoal.
- Todas as rotas de dominio usam escopo por organizacao.
- Header opcional para selecionar tenant: `X-Organization-Id: <id>`
  - sem header, usa a primeira membership do usuario.

## RBAC por acao

- Permissoes aplicadas por role (`owner`, `admin`, `member`) por endpoint/acao.
- `member` possui permissoes operacionais (listar/criar/atualizar) e nao pode executar acoes destrutivas sensiveis (ex.: deletes de subject/task).
- Endpoints internos exigem permissoes especificas (`internal:email_queue:view/process`), efetivamente restritos a `owner/admin`.

## Auth profissional (P0)

- Access token + refresh token com rotacao.
- Revogacao de access token no logout (blacklist por `jti`).
- Sessao de refresh persistida em banco (`auth_sessions`).
- Rate limit persistente para `login`, `refresh` e `logout`.
- Verificacao de email com action token expiravel e uso unico.
- Recuperacao de senha com action token expiravel e invalidacao de sessoes ativas.

## Email transacional + fila assincrona

- Provider suportado:
  - `EMAIL_PROVIDER=console` (dev)
  - `EMAIL_PROVIDER=smtp`
  - `EMAIL_PROVIDER=resend`
- Requests de verificacao/reset entram na tabela `email_jobs`.
- Worker processa fila com retry exponencial.

Rodar worker:

```bash
python -m app.workers.email_worker
```

Observabilidade:
- `GET /internal/email-queue/stats`
- `POST /internal/email-queue/process`
- endpoints internos exigem role `owner` ou `admin` no tenant selecionado.

## Observabilidade

- `X-Request-Id` em todas as respostas.
- logs estruturados por request (json line).
- captura de excecoes 500 com `request_id`.
- integracao opcional com Sentry via:
  - `SENTRY_DSN`
  - `SENTRY_TRACES_SAMPLE_RATE`

## Finalizacao de sessao (recomendado)

Use `POST /sessions/finalize` para encapsular regras:

```json
{
  "source": "manual",
  "completed_tasks": 1,
  "study_minutes": 35,
  "focus_score": 80,
  "time_block": "19:00-21:00"
}
```

Para revisao:

```json
{
  "source": "review",
  "study_minutes": 25,
  "quality": 4,
  "time_block": "19:00-21:00"
}
```

O backend acumula os eventos no dia automaticamente.
