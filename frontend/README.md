# StudyOS Frontend

App Next.js do StudyOS com:

- landing page publica
- auth
- dashboard
- planner
- study session
- reviews
- analytics
- configuracoes da organizacao

## Executar localmente

```bash
copy .env.example .env.local
npm install
npm run dev
```

URL local padrao: `http://127.0.0.1:3000`

`.env.example` ja aponta para a API local:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8010
```

Se a variavel nao for definida, o frontend faz fallback para `http://127.0.0.1:8010` apenas quando aberto em `localhost` ou `127.0.0.1`.

Em Vercel, `NEXT_PUBLIC_API_BASE_URL` precisa ser configurada explicitamente para o dominio publico do backend.

## Testes E2E

```bash
npx playwright install chromium
npm run test:e2e
```

Cobertura atual:

- registro
- login
- finalizar sessao
- responder revisao
- administracao de membros

## Deploy

As variaveis e exemplos de configuracao estao em [../DEPLOYMENT.md](../DEPLOYMENT.md).
