# ReembolsaBR API

Backend SaaS multiempresa para submissão, validação e aprovação de despesas corporativas. O domínio começa com documentos brasileiros, sem fixar país ou moeda na arquitetura.

## Recursos

- FastAPI, Pydantic v2 e SQLAlchemy 2 com PostgreSQL;
- JWT, usuários multiempresa e papéis `employee`, `approver` e `admin`;
- fluxo `draft → submitted → approved/rejected/reimbursed`;
- extração inicial de CNPJ, chave NF-e, data e valor por regex;
- duplicidade por chave fiscal ou pela combinação CNPJ/data/valor dentro da empresa;
- políticas configuráveis por categoria e país (exemplo: alimentação até BRL 150);
- trilha de auditoria para criação e mudanças de estado;
- Celery/Redis para processamento assíncrono de comprovantes;
- migrações Alembic, Docker Compose e testes unitários.

## Arquitetura

```text
app/
├── api/routes/       # HTTP: auth, despesas, políticas e auditoria
├── core/             # configuração, JWT e RBAC
├── db/               # engine, sessão e base declarativa
├── models/           # entidades SQLAlchemy
├── parsers/          # parsers fiscais extensíveis por país
├── schemas/          # contratos Pydantic
├── services/         # regras de negócio
└── tasks/            # jobs Celery
```

Toda entidade de negócio carrega `organization_id`. Valores usam `Numeric`, datas são separadas de timestamps, e `country_code`/`currency` permitem acrescentar parsers e políticas de outros países.

## Execução com Docker

1. Copie a configuração: `cp .env.example .env` (troque `SECRET_KEY` em produção).
2. Suba e migre: `docker compose up --build -d`.
3. Abra Swagger em http://localhost:8000/docs e health check em http://localhost:8000/health.

O container da API executa `alembic upgrade head` antes do Uvicorn. Para acompanhar: `docker compose logs -f api worker`.

## Fluxo de exemplo

Crie a primeira organização e seu administrador (endpoint público apenas para bootstrap):

```bash
curl -X POST localhost:8000/api/v1/auth/register -H 'Content-Type: application/json' \
  -d '{"organization_name":"Acme Brasil","email":"admin@acme.com","password":"Senha-forte-123"}'
```

Obtenha o token:

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/token -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@acme.com&password=Senha-forte-123' | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
```

Crie uma política e uma despesa:

```bash
curl -X POST localhost:8000/api/v1/policies -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"category":"meals","country_code":"BR","currency":"BRL","max_amount":150}'

curl -X POST localhost:8000/api/v1/expenses -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"category":"meals","amount":89.90,"currency":"BRL","expense_date":"2026-08-14","merchant_tax_id":"12.345.678/0001-90","invoice_key":"12345678901234567890123456789012345678901234","country_code":"BR"}'
```

Use `POST /expenses/{id}/submit`; aprovadores/admins usam `/approve`, `/reject` e `/reimburse`. Consulte `/audit-logs` (admin). O endpoint `/expenses/parse-receipt` demonstra o parser; em produção, OCR deve produzir o texto antes desta etapa.

## Desenvolvimento local

Requer Python 3.12, PostgreSQL e Redis:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
celery -A app.worker.celery_app worker --loglevel=info
```

Qualidade e testes:

```bash
pytest
ruff check .
```

## Segurança e próximos passos

O registro é um bootstrap propositalmente simples; desabilite-o ou proteja-o por convite após criar o primeiro tenant. Use segredo gerenciado, TLS, rotação/revogação de tokens, rate limiting e storage privado de comprovantes em produção. Evoluções naturais incluem OCR, integração bancária/ERP, LGPD (retenção e anonimização), refresh tokens, SSO/MFA, alçadas de aprovação e regras tributárias por país.

## API

- `POST /api/v1/auth/register`, `POST /api/v1/auth/token`
- `GET/POST /api/v1/expenses`, ações de workflow e parser
- `GET/POST /api/v1/policies`
- `GET /api/v1/audit-logs` (admin)
- `GET /health`
