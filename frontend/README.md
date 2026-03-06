# StudyOS Frontend (Next.js)

Interface SaaS completa do StudyOS com:
- Landing page pública
- Auth (`/auth/login`, `/auth/register`)
- Dashboard com trend + heatmap + evolution score
- Planner adaptativo
- Study Session com timer
- Review com automação de `POST /sessions/finalize`
- Analytics avançado
- Library (subjects/tasks)
- Goals
- Settings (admin da organização + billing + account)

## Executar local

```bash
npm install
npm run dev
```

App padrão: `http://127.0.0.1:3000`

## Testes E2E (Playwright)

```bash
npx playwright install chromium
npm run test:e2e
```

Cobertura atual:
- registro
- login
- finalizar sessão
- responder revisão
- administração de membros (convidar, trocar role, remover)

## Variáveis úteis

- `NEXT_PUBLIC_API_BASE_URL` (ex: `http://127.0.0.1:8010`)

Se não for definida, o frontend usa:
- `http://127.0.0.1:8010` em localhost
- `https://studyos-api-staging.up.railway.app` fora de localhost

## Segurança de dependências

`next` atualizado para versão corrigida (`15.5.10`) para remover advisory de alta severidade reportado por `npm audit`.
