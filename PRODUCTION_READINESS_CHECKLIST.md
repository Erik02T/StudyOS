# StudyOS Production Readiness Checklist

Checklist executavel para evoluir o MVP para SaaS profissional.

## P0 - Obrigatorio antes de producao publica

- [x] Separacao backend/frontend em monorepo.
- [x] Base multi-tenant: organizations + memberships.
- [x] Escopo por tenant nas rotas principais via `X-Organization-Id`.
- [x] Versionamento de API (`/v1`) com compatibilidade.
- [x] Refresh token + revogacao de sessao.
- [x] Rate limit em login/refresh/logout.
- [x] Recuperacao de senha e verificacao de email.
- [ ] Segredos por ambiente (dev/staging/prod) em secret manager.
- [ ] Observabilidade: logs estruturados + error tracking.
- [ ] CI/CD com gate de testes e migracoes.
- [ ] Backup/restore automatizado de banco.

## P1 - Confiabilidade operacional

- [ ] RBAC por organizacao (owner/admin/member).
- [ ] Auditoria de eventos (`study_events`).
- [ ] Jobs assincronos para lembretes/reprocessamento.
- [ ] Idempotencia para endpoints de sessao.
- [ ] Testes de integracao com Postgres em pipeline.

## P2 - Escala de produto

- [ ] Billing (Free/Pro) com limites por tenant.
- [ ] Dashboards administrativos (MRR, churn, retention).
- [ ] IA com explicabilidade e fallback deterministico.
- [ ] Integracoes externas (Notion/Anki/API publica).

## Entregas tecnicas da iteracao atual

- Multi-tenant foundation:
  - `backend/app/models/organization.py`
  - `backend/app/models/membership.py`
  - `backend/alembic/versions/20260305_0003_multi_tenant_foundation.py`
- Tenant scoping:
  - `backend/app/core/security.py` (`get_current_organization`)
  - rotas de `subjects`, `tasks`, `planner`, `reviews`, `analytics`, `sessions`
- Provisionamento inicial:
  - `backend/app/routers/auth.py` cria workspace pessoal no registro.
