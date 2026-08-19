# Opção B - Deploy no Railway ou Render

## Status
✅ Projeto compatível nativamente
✅ Dockerfile já configurado
✅ docker-compose.yml disponível

## Por que Railway/Render?
- Suporte completo a aplicações Python/FastAPI
- PostgreSQL gerenciado integrado
- Redis gerenciado para Celery
- Background tasks funcionam normalmente
- Sem limitações serverless
- Deploy automático via GitHub

---

## 🚀 Railway

### Passo 1: Preparar Repositório
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### Passo 2: Criar Projeto no Railway
1. Acesse https://railway.app
2. Clique em "New Project"
3. Selecione "Deploy from GitHub repo"
4. Escolha o repositório do ReembolsaBR

### Passo 3: Configurar Serviços

#### Serviço Principal (App)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Port**: 8000 (ou variável $PORT)

#### Banco de Dados
1. Adicionar serviço: PostgreSQL
2. Railway cria automaticamente
3. Copiar `DATABASE_URL` das variáveis

#### Redis (para Celery)
1. Adicionar serviço: Redis
2. Copiar `REDIS_URL` das variáveis

### Passo 4: Variáveis de Ambiente
No Railway Dashboard, configurar:
```bash
DATABASE_URL=postgresql://...
SECRET_KEY=sua-chave-secreta-forte
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://...
ENVIRONMENT=production
```

### Passo 5: Rodar Migrações
```bash
# No Railway CLI ou terminal do serviço
alembic upgrade head
```

### Passo 6: Deploy do Worker (Celery)
Criar novo serviço no Railway:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `celery -A app.worker worker --loglevel=info`
- Mesmas variáveis de ambiente do app principal

---

## 🎨 Render

### Passo 1: Criar Web Service
1. Acesse https://render.com
2. New → Web Service
3. Conectar repositório GitHub

### Passo 2: Configurar Web Service
```yaml
Name: reembolsabr-api
Environment: Python 3
Build Command: pip install -r requirements.txt && alembic upgrade head
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Passo 3: Adicionar PostgreSQL
1. New → Database → PostgreSQL
2. Aguardar provisionamento
3. Copiar connection string interna

### Passo 4: Adicionar Redis
1. New → Redis
2. Copiar URL de conexão

### Passo 5: Variáveis de Ambiente
```bash
DATABASE_URL=<postgres-internal-url>
SECRET_KEY=<gerar-uma-chave-forte>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=<redis-url>
```

### Passo 6: Criar Background Worker
1. New → Background Worker
2. Build: `pip install -r requirements.txt`
3. Start: `celery -A app.worker worker --loglevel=info`

---

## Comparação Railway vs Render

| Feature | Railway | Render |
|---------|---------|--------|
| PostgreSQL | ✅ Incluído | ✅ Incluído |
| Redis | ✅ Incluído | ✅ Incluído |
| Background Workers | ✅ Nativo | ✅ Nativo |
| Deploy Automático | ✅ GitHub | ✅ GitHub |
| Plano Gratuito | $5 crédito/mês | Limitado mas funcional |
| Facilidade | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## Comandos Úteis

### Railway CLI
```bash
npm i -g @railway/cli
railway login
railway link
railway up
railway logs
```

### Render CLI
```bash
# Usar dashboard web ou API
# CLI menos comum, maioria via UI
```

---

## Checklist Final

- [ ] Código no GitHub (branch main)
- [ ] Variáveis de ambiente configuradas
- [ ] PostgreSQL provisionado
- [ ] Redis provisionado (se usar Celery)
- [ ] Migrações rodadas (`alembic upgrade head`)
- [ ] Worker Celery deployado
- [ ] Testar endpoint `/health`
- [ ] Testar autenticação
- [ ] Testar upload de recibos

---
