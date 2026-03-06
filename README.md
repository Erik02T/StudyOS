# StudyOS Monorepo

> Status: Em construcao.

Projeto separado em duas pastas:

- `backend/`: API FastAPI + PostgreSQL + motores adaptativos.
- `frontend/`: painel React para dashboard e operacao diaria.
- `PRODUCTION_READINESS_CHECKLIST.md`: plano executavel para maturidade SaaS.
- `RUNBOOK_STAGING.md`: procedimentos operacionais para incidentes em staging.

## Melhorias SaaS recentes

- Idempotencia em `POST /sessions/finalize` via header `Idempotency-Key`.
- Trilha de auditoria com eventos em `GET /analytics/events`.
- Hardening de seguranca (headers HTTP + CORS por ambiente).

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Banco local com Docker

```bash
docker compose up -d db
cd backend
python -m alembic upgrade head
```

## Start/Stop com um comando

PowerShell (na raiz do projeto):

```powershell
.\start-prod-local.ps1
```

Para reiniciar processos existentes:

```powershell
.\start-prod-local.ps1 -ForceRestart
```

Para parar API + worker + banco:

```powershell
.\stop-prod-local.ps1
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## Fluxo automatizado no app

- Ao finalizar revisao no frontend, o app chama:
1. `POST /reviews/answer`
2. `POST /sessions/finalize` com `source=review`

- Ao finalizar sessao no frontend, o app chama:
1. `POST /sessions/finalize` com `source=manual`
