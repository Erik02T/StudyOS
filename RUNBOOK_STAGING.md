# StudyOS Staging Runbook

## 1. Health checks

- Backend: `GET /health`
- Frontend: load main URL and verify login/register form renders.
- If backend is down, check latest deploy logs in Railway.
- If frontend is down, check Vercel deployment logs and failed build step.

## 2. CORS incident

Symptoms:
- Browser error: `blocked by CORS policy`
- Requests fail on preflight (`OPTIONS`) before hitting endpoint logic.

Actions:
1. Confirm backend `CORS_ORIGINS` includes frontend domain(s).
2. Confirm `CORSMiddleware` is enabled in `backend/app/main.py`.
3. Redeploy backend and re-test with browser hard refresh.

## 3. Auth incident

Symptoms:
- Register/login failing with `401/429/400`.

Actions:
1. Check `/auth/register` and `/auth/login` response body for `detail`.
2. Validate `SECRET_KEY` is configured and stable between deploys.
3. Verify rate-limit thresholds:
   - `LOGIN_RATE_LIMIT`
   - `LOGIN_RATE_WINDOW_SECONDS`
4. For flood/abuse, keep rate-limit strict; for false positives, tune limits.

## 4. Migration incident

Symptoms:
- API starts but fails DB operations.
- Alembic head mismatch in CI.

Actions:
1. Run `python -m alembic heads` and ensure single head.
2. Run `python -m alembic upgrade head`.
3. If failed migration, inspect latest revision in `backend/alembic/versions`.

## 5. Deployment rollback

Backend:
1. Open Railway service deployment history.
2. Roll back to last healthy deployment.
3. Re-run `/health` and smoke auth endpoints.

Frontend:
1. Open Vercel deployment history.
2. Promote last healthy deployment to production/staging alias.
3. Validate login/register flow.

## 6. Post-incident checklist

1. Open issue with root cause + timeline.
2. Add regression test in `backend/tests` or frontend flow tests.
3. Update this runbook if a new class of incident appears.
