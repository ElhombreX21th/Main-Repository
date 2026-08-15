# ReembolsaBR API

Backend SaaS multiempresa para submissão, validação e aprovação de despesas corporativas. O domínio começa com documentos brasileiros, sem fixar país ou moeda na arquitetura.

## Recursos

- FastAPI, Pydantic v2 e SQLAlchemy 2 com PostgreSQL;
- JWT, usuários multiempresa e papéis `employee`, `approver` e `admin`;
- criação de usuários `employee` e `approver` por administradores;
- fluxo `draft → submitted → approved/rejected/reimbursed`;
- extração inicial de CNPJ, chave NF-e, data e valor por regex;
- duplicidade por chave fiscal ou pela combinação CNPJ/data/valor dentro da empresa;
- políticas configuráveis por categoria e país (exemplo: alimentação até BRL 150);
- trilha de auditoria para criação e mudanças de estado;
- aprovação em duas alçadas para despesas acima de BRL 5.000;
- upload privado de comprovantes de até 5 MB e processamento assíncrono extensível para OCR;
- refresh tokens com rotação e proteção contra replay;
- exportação LGPD, anonimização da conta, relatórios e exportação para ERP;
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

A interface web fica disponível em **http://localhost:8000/**. Ela inclui autenticação, cadastro da
empresa, dashboard responsivo, criação e acompanhamento de despesas, aprovações, políticas,
relatórios e gestão da equipe. Não há build separado: os assets são servidos diretamente pela API.

### Visualização imediata, sem Docker

#### Windows — dois cliques

Depois de aplicar ou baixar os arquivos, dê dois cliques em **`ABRIR_DEMO.bat`** na pasta do
projeto. Alternativamente, abra diretamente **`app/web/demo.html`**. Essa opção funciona como um
arquivo local: não usa servidor, terminal, Docker ou instalação de dependências.

#### Preview com servidor local

Para conhecer a interface com dados demonstrativos por um servidor local, execute:

```bash
python scripts/preview_ui.py
```

Abra **http://127.0.0.1:4173/demo**. O modo demonstração permite navegar pelo dashboard, despesas,
aprovações, relatórios, políticas e equipe sem gravar dados. Com a aplicação completa em execução,
`http://localhost:8000/demo` oferece a mesma apresentação e `/` usa os dados reais da API.

### Publicação na Vercel

O `vercel.json` publica somente a demonstração web e abre o modo demo automaticamente no domínio
`*.vercel.app`. Depois de autenticar a CLI (`npx vercel login`), publique com:

```bash
npx vercel --prod
```

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

Administradores criam os demais usuários do tenant em `POST /api/v1/users`:

```bash
curl -X POST localhost:8000/api/v1/users -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"email":"aprovador@acme.com","password":"Senha-forte-123","role":"approver"}'
```

A proteção contra duplicidade existe tanto no serviço quanto no banco. Dentro de uma mesma
organização, não podem existir duas despesas com a mesma chave fiscal nem com a mesma combinação
de CNPJ, data e valor. Violações concorrentes das constraints retornam HTTP `409`.

## Aprovações e comprovantes

Ao enviar uma despesa, o sistema cria uma aprovação; despesas acima de BRL 5.000 criam duas
alçadas sequenciais. Ações em `/{id}/approve` e `/{id}/reject` aceitam
`{"comment":"Justificativa"}`. Comprovantes JPEG, PNG, PDF ou texto de até 5 MB podem ser enviados
como multipart em `POST /api/v1/expenses/{id}/receipt`. O volume `receipt_data` mantém os arquivos;
em produção, substitua-o por object storage privado com criptografia e URLs temporárias.

## Segurança, privacidade e integrações

- `POST /api/v1/auth/refresh` rotaciona o refresh token; um token utilizado não pode ser repetido;
- `GET /api/v1/privacy/me/export` entrega os dados do titular e `DELETE /privacy/me` anonimiza a conta;
- `GET /api/v1/reports/expenses?start=YYYY-MM-DD&end=YYYY-MM-DD` agrega despesas por categoria;
- `GET /api/v1/integrations/erp/approved-expenses` fornece lançamentos aprovados para integração;
- a trilha de auditoria registra alterações relevantes dentro do tenant.

O parser atual recebe texto. OCR real deve ser conectado ao job Celery `receipts.parse_br`, evitando
processamento pesado no request da API.

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

O registro é um bootstrap propositalmente simples; desabilite-o ou proteja-o por convite após criar
o primeiro tenant. Em produção, use segredo gerenciado, TLS, rate limiting, object storage privado,
políticas formais de retenção, SSO/MFA e conectores homologados para cada ERP ou instituição
financeira.

## API

- `POST /api/v1/auth/register`, `POST /api/v1/auth/token`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/users` (admin; cria employee/approver)
- `GET/POST /api/v1/expenses`, ações de workflow e parser
- `GET/POST /api/v1/policies`
- `GET /api/v1/audit-logs` (admin)
- `GET /api/v1/reports/expenses`, `GET /api/v1/integrations/erp/approved-expenses`
- `GET /api/v1/privacy/me/export`, `DELETE /api/v1/privacy/me`
- `GET /health`
