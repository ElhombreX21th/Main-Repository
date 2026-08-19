# Opção A - Deploy na Vercel

## Status
✅ `vercel.json` criado e configurado
⚠️ Plugin Vercel indisponível nesta sessão
⚠️ CLI da Vercel bloqueada (403 Forbidden)

## Arquivo vercel.json
Configurado com:
- Runtime Python 3.11
- Build usando `@vercel/python`
- Rotas direcionadas para `app/main.py`

## Pré-requisitos
1. Plugin Vercel conectado na sessão
2. Conta Vercel autenticada
3. Projeto vinculado a um repositório GitHub

## Comandos para deploy (após conectar plugin)
```bash
# Via CLI (se disponível)
npx --yes vercel@latest --yes --prod

# Ou via Dashboard Vercel
# 1. Importar repositório do GitHub
# 2. Configurar variáveis de ambiente
# 3. Deploy automático
```

## Variáveis de Ambiente Necessárias
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Chave para JWT
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiração do token
- `REDIS_URL`: Redis para Celery (opcional)

## Limitações Identificadas
- **Celery/Redis**: Não funciona nativamente na Vercel (serverless)
- **PostgreSQL**: Precisa de serviço externo (Neon, Supabase, etc.)
- **WebSockets/Long polling**: Limitado em serverless
- **Background tasks**: Requer adaptação para Vercel Functions

## Adaptações Sugeridas
1. Substituir Celery por Vercel Cron + API Routes
2. Usar banco de dados serverless (Neon, PlanetScale, Supabase)
3. Mover processamento pesado para funções serverless separadas

---
