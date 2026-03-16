# StudyOS Monorepo

Monorepo com:

- `backend/`: API FastAPI + PostgreSQL + workers.
- `frontend/`: app Next.js.
- `DEPLOYMENT.md`: variaveis e configuracao para Railway + Vercel.
- `RUNBOOK_STAGING.md`: resposta operacional para incidentes.
- `PRODUCTION_READINESS_CHECKLIST.md`: backlog de maturidade SaaS.

## URLs locais padrao

- Frontend: `http://127.0.0.1:3000`
- Backend: `http://127.0.0.1:8010`
- Healthcheck: `http://127.0.0.1:8010/health`
- PostgreSQL via Docker Compose: `127.0.0.1:5433`

## Subir tudo localmente

PowerShell na raiz do projeto:

```powershell
.\start-prod-local.ps1
```

O script:

- valida se o Docker Desktop esta rodando
- sobe o Postgres local
- roda as migracoes
- inicia API + worker
- espera o `GET /health` responder antes de concluir

Para reiniciar processos existentes:

```powershell
.\start-prod-local.ps1 -ForceRestart
```

Para parar API + worker + banco:

```powershell
.\stop-prod-local.ps1
```

## Backend manual

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

## Frontend manual

```bash
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

`frontend/.env.example` ja aponta para `http://127.0.0.1:8010`.

## Fluxo automatizado no app

- Ao finalizar revisao no frontend, o app chama `POST /reviews/answer` e depois `POST /sessions/finalize` com `source=review`.
- Ao finalizar sessao no frontend, o app chama `POST /sessions/finalize` com `source=manual`.

## Deploy

Consulte [DEPLOYMENT.md](DEPLOYMENT.md) para as variaveis que precisam ser configuradas no Railway e no Vercel.
