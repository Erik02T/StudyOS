# StudyOS Frontend

Painel React com:
- trend chart de produtividade
- heatmap por horario
- evolution score
- finalizacao de revisoes e sessoes com envio automatico para analytics

## Executar

```bash
npm install
npm run dev
```

## Configuracao no app

- API Base: ex. `http://127.0.0.1:8000`
- Email e senha para:
  - `Entrar` via `/auth/login`
  - `Criar conta` via `/auth/register`

O frontend chama `POST /sessions/finalize` automaticamente ao finalizar revisoes e sessoes.
