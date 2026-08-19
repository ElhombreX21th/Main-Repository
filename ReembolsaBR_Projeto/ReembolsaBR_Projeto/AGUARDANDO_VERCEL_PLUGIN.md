# Opção C - Aguardar Plugin Vercel

## Status Atual
⏸️ **Aguardando reconexão do plugin Vercel**

### O que já está pronto:
- ✅ `vercel.json` configurado
- ✅ Código no Git (repositório limpo)
- ✅ Estrutura do projeto organizada
- ✅ Documentação de deploy criada

---

## Próximos Passos (Após Reconectar Plugin)

### 1. Verificar Ferramentas Disponíveis
```bash
# Listar ferramentas Vercel disponíveis
# (será automático na nova sessão com plugin)
```

### 2. Autenticar na Vercel
```bash
vercel login
```

### 3. Link do Projeto
```bash
vercel link
# Ou criar novo projeto
vercel
```

### 4. Configurar Variáveis de Ambiente
No Dashboard da Vercel ou via CLI:
```bash
vercel env add DATABASE_URL production
vercel env add SECRET_KEY production
vercel env add ACCESS_TOKEN_EXPIRE_MINUTES production
```

### 5. Deploy
```bash
vercel --prod
```

---

## Limitações a Considerar (Vercel)

### ❌ Não Compatível Nativamente
| Componente | Problema | Solução |
|------------|----------|---------|
| Celery | Requer worker contínuo | Migrar para Vercel Cron + Functions |
| Redis | Serviço externo necessário | Usar Redis cloud (Upstash, etc.) |
| PostgreSQL | Precisa ser externo | Neon, Supabase, PlanetScale |
| Upload de arquivos | Limite 6MB serverless | Usar S3/R2 + presigned URLs |

### ⚠️ Adaptações Necessárias

#### 1. Background Tasks (Celery → Vercel Functions)
```python
# De:
from celery import Celery
@app.task
def process_receipt(file_id): ...

# Para:
from vercel.functions import task
@task
async def process_receipt(file_id): ...
```

#### 2. Banco de Dados
Recomendado migrar para:
- **Neon** (PostgreSQL serverless)
- **Supabase** (PostgreSQL + extras)
- **PlanetScale** (MySQL compatível)

#### 3. Redis
Substituir por:
- **Upstash Redis** (serverless Redis)
- **Vercel KV** (Redis-compatible)

---

## Checklist Pré-Deploy Vercel

- [ ] Plugin Vercel conectado
- [ ] `vercel.json` revisado
- [ ] Dependências compatíveis (sem Celery se não adaptar)
- [ ] Banco de dados serverless configurado
- [ ] Redis serverless configurado (se necessário)
- [ ] Variáveis de ambiente definidas
- [ ] Testes locais com `vercel dev`
- [ ] Code push para branch main

---

## Comandos de Desenvolvimento Local

```bash
# Instalar Vercel CLI globalmente
npm i -g vercel

# Login
vercel login

# Desenvolvimento local com hot-reload
vercel dev

# Deploy de preview (staging)
vercel

# Deploy para produção
vercel --prod

# Logs em tempo real
vercel logs --follow

# Listar deployments
vercel ls
```

---

## Fluxo Recomendado

1. **Desenvolvimento**: `vercel dev` localmente
2. **Preview**: Push para branch → Deploy automático de preview
3. **Produção**: Merge para main → `vercel --prod` ou auto-deploy

---

## Links Úteis

- [Vercel Python Runtime](https://vercel.com/docs/runtimes/python)
- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Vercel Serverless Functions](https://vercel.com/docs/functions/serverless-functions)
- [Vercel Cron Jobs](https://vercel.com/docs/cron-jobs)

---

## Nota Importante

> ⚠️ **Esta sessão atual NÃO tem acesso às ferramentas Vercel.**
> 
> É necessário **reiniciar/reabrir a tarefa** após conectar o plugin Vercel
> para que as ferramentas sejam injetadas na nova sessão.
>
> Enquanto isso, use os guias **DEPLOY_VERCEL.md** ou **DEPLOY_RAILWAY_RENDER.md**
> conforme sua escolha de plataforma.

---
