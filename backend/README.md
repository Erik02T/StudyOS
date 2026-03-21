# StudyOS Backend

API FastAPI do StudyOS com:

- auth JWT com refresh token rotativo
- multi-tenant por organizacao
- CRUD de subjects/tasks
- planner adaptativo
- reviews com spaced repetition
- analytics e billing foundation

## Executar localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

URLs locais:

- API: `http://127.0.0.1:8080`
- Healthcheck: `http://127.0.0.1:8080/health`

Defaults importantes no `.env.example`:

- `DATABASE_URL=postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/studyos`
- `PUBLIC_APP_URL=http://127.0.0.1:3000`
- `CORS_ORIGINS` com origins locais (`3000` e `5173`)
- `CORS_ALLOW_ORIGIN_REGEX=^https:\/\/.*\.vercel\.app$` para previews e deploys Vercel
- `EMAIL_PROVIDER=console` para desenvolvimento local

## Testes

```bash
python -m pytest -q
```

## Endpoints principais

- `GET /health`
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

Todos eles tambem existem com prefixo versionado em `/v1/...`.

## Deploy

As variaveis obrigatorias para Railway e Vercel estao em [../DEPLOYMENT.md](../DEPLOYMENT.md).
