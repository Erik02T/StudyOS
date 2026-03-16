# Deployment Guide

## Arquitetura esperada

- Backend: Railway
- Frontend: Vercel
- Banco local: Docker Compose em `127.0.0.1:5433`

## Defaults locais do repositorio

- Frontend local: `http://127.0.0.1:3000`
- Backend local: `http://127.0.0.1:8080`
- Healthcheck: `http://127.0.0.1:8080/health`

## Railway: backend

Variaveis minimas recomendadas para cada ambiente:

- `APP_ENV=staging` ou `APP_ENV=production`
- `SECRET_KEY=<gere um valor forte e estavel>`
- `DATABASE_URL=<connection string do Postgres do ambiente>`
- `PUBLIC_APP_URL=<URL publica do frontend desse ambiente>`
- `CORS_ORIGINS=<lista de frontends autorizados, separada por virgula>`
- `CORS_ALLOW_ORIGIN_REGEX=^https:\/\/.*\.vercel\.app$`

Variaveis de email:

- staging: `EMAIL_PROVIDER=console`
- producao com Resend:
  - `EMAIL_PROVIDER=resend`
  - `EMAIL_FROM=<remetente valido>`
  - `EMAIL_RESEND_API_KEY=<token>`
- producao com SMTP:
  - `EMAIL_PROVIDER=smtp`
  - `EMAIL_FROM=<remetente valido>`
  - `EMAIL_SMTP_HOST=<host>`
  - `EMAIL_SMTP_PORT=<porta>`
  - `EMAIL_SMTP_USERNAME=<usuario>`
  - `EMAIL_SMTP_PASSWORD=<senha>`
  - `EMAIL_SMTP_USE_TLS=true`

Variaveis opcionais:

- `APP_NAME=StudyOS API`
- `APP_VERSION=<versao do deploy>`
- `LOG_LEVEL=INFO`
- `JSON_LOGS_ENABLED=true`
- `SENTRY_DSN=<dsn>`
- `SENTRY_TRACES_SAMPLE_RATE=0.2`
- `STRIPE_SECRET_KEY=<token>`
- `STRIPE_WEBHOOK_SECRET=<secret>`
- `STRIPE_PRICE_PRO_MONTHLY=<price_id>`

Exemplo de producao:

- `PUBLIC_APP_URL=https://study-os-xi.vercel.app`
- `CORS_ORIGINS=https://study-os-xi.vercel.app`

Exemplo de staging:

- `PUBLIC_APP_URL=https://studyos-staging.vercel.app`
- `CORS_ORIGINS=https://studyos-staging.vercel.app`

Se o mesmo backend precisar aceitar mais de um frontend, use lista CSV:

```text
CORS_ORIGINS=https://study-os-xi.vercel.app,https://studyos-staging.vercel.app
```

Depois de alterar variaveis no Railway:

1. Rode `python -m alembic upgrade head` no deploy ou no release command.
2. Redeploy o servico.
3. Valide `GET /health`.
4. Teste `POST /auth/register` e `POST /auth/login`.

## Vercel: frontend

Variavel obrigatoria:

- `NEXT_PUBLIC_API_BASE_URL=<URL publica do backend Railway>`

Exemplo de producao:

- `NEXT_PUBLIC_API_BASE_URL=https://<seu-backend-prod>.up.railway.app`

Exemplo de staging:

- `NEXT_PUBLIC_API_BASE_URL=https://<seu-backend-staging>.up.railway.app`

Depois de alterar variaveis no Vercel:

1. Redeploy o projeto.
2. Abra a pagina de login.
3. Confirme no navegador que as chamadas vao para `NEXT_PUBLIC_API_BASE_URL`.

## Checklist rapido depois do deploy

1. Backend responde em `/health`.
2. Frontend carrega sem erro de `NEXT_PUBLIC_API_BASE_URL`.
3. Register/login funcionam.
4. Nao ha erro de CORS no navegador.
5. Links de verificacao e reset apontam para o frontend correto via `PUBLIC_APP_URL`.
