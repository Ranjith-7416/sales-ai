# Sales AI - Production Deployment Guide

This guide provides step-by-step instructions for deploying the Sales AI application to production environments using Render (backend) and Vercel (frontend). The repository currently contains deployment instructions, not completed production URLs.

## Table of Contents

1. [Backend Deployment (Render)](#backend-deployment-render)
2. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Troubleshooting](#troubleshooting)

---

## Backend Deployment (Render)

### Prerequisites
- Render account (https://render.com)
- GitHub repository with your Sales AI code
- PostgreSQL database (Render can provide)
- Redis instance (Render can provide)
- API keys for LLM providers (Anthropic, OpenAI, Google, OpenRouter, or Groq)
- Search API keys (Brave Search, Serper)

### Step 1: Create PostgreSQL Database

1. Log in to Render dashboard
2. Click "New +" → "PostgreSQL"
3. Configure:
   - **Name**: `sales-ai-postgres`
   - **Database**: `salesai_db`
   - **User**: `salesai`
   - **Region**: Choose closest to your users
   - **Pricing Tier**: Choose based on expected load (Standard starts at ~$15/month)
4. Click "Create Database"
5. Copy the internal connection string for backend configuration

### Step 2: Create Redis Instance

1. Click "New +" → "Redis"
2. Configure:
   - **Name**: `sales-ai-redis`
   - **Region**: Same as PostgreSQL
   - **Pricing Tier**: Free tier available for testing
3. Click "Create Redis"
4. Copy the connection URL

### Step 3: Create Backend Web Service

1. Click "New +" → "Web Service"
2. Connect to your GitHub repository containing the Sales AI code
3. Configure:
   - **Name**: `sales-ai-backend`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000`
4. Click "Create Web Service"

### Step 4: Configure Environment Variables

In Render dashboard, go to your backend service → Environment:

```
# LLM Configuration
LLM_PROVIDER=groq
LLM_MODEL_MAIN=gemini-3.6-flash
LLM_MODEL_REASONING=gemini-3.6-flash
GROQ_API_KEY=your_groq_key
# To select Groq instead, set LLM_PROVIDER=groq and configure:
# GROQ_MODEL_MAIN=openai/gpt-oss-120b
# GROQ_MODEL_REASONING=openai/gpt-oss-120b
# To select OpenRouter instead, replace LLM_PROVIDER with openrouter and set:
# OPENROUTER_API_KEY=your_openrouter_key
# OPENROUTER_MODEL_MAIN=provider/model-id
# OPENROUTER_MODEL_REASONING=provider/model-id
# To select Gemini instead, replace LLM_PROVIDER with gemini and set:
# GOOGLE_API_KEY=your_google_key
# Anthropic remains optional when selected explicitly.
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# Web Search
BRAVE_API_KEY=your_brave_key
SERPER_API_KEY=your_serper_key

# Database (from Render PostgreSQL)
DATABASE_URL=your_internal_postgres_connection_string
# For Docker development, Compose uses POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB
# to build the internal service URL for the backend.

# Redis (from Render Redis)
REDIS_URL=your_redis_connection_string
REDIS_TIMEOUT_SECONDS=5

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-frontend-domain.com
API_AUTH_TOKEN=your_backend_api_token
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_LEAD_REQUESTS=10
RATE_LIMIT_PROPOSAL_REQUESTS=30
RATE_LIMIT_KB_UPLOADS=10
WEB_SEARCH_TIMEOUT_SECONDS=15
LLM_TIMEOUT_SECONDS=120
DATABASE_CONNECT_TIMEOUT_SECONDS=10
KNOWLEDGE_BASE_PATH=/tmp/knowledge_base
```

### Step 5: Deploy

1. Render automatically deploys on push to main branch
2. Monitor deployment in "Logs" tab
3. Once deployed, note the backend URL (e.g., `https://sales-ai-backend.onrender.com`)

---

## Frontend Deployment (Vercel)

### Prerequisites
- Vercel account (https://vercel.com)
- GitHub repository
- Backend URL from Render deployment

### Step 1: Connect GitHub Repository

1. Log in to Vercel
2. Click "Add New..." → "Project"
3. Select your GitHub repository
4. Vercel will auto-detect Next.js/React project

### Step 2: Configure Build Settings

1. **Framework Preset**: Vite
2. **Build Command**: `npm run build`
3. **Output Directory**: `dist`
4. **Install Command**: `npm ci`
5. Project Root: `frontend`

### Step 3: Configure Environment Variables

Add in Vercel project settings → Environment Variables:

```
VITE_API_URL=https://sales-ai-backend.onrender.com/api
VITE_API_TOKEN=your_backend_api_token
```

### Step 4: Deploy

1. Click "Deploy"
2. Vercel automatically builds and deploys
3. Once complete, note the frontend URL

### Step 5: Update Backend CORS

Update backend environment variable in Render:
```
CORS_ORIGINS=https://your-vercel-frontend.vercel.app,https://your-custom-domain.com
```

---

## Environment Configuration

### API Keys Required

#### 1. Anthropic Claude
- Go to: https://console.anthropic.com
- Create API key
- Set `ANTHROPIC_API_KEY`

#### 2. OpenAI (Optional fallback)
- Go to: https://platform.openai.com/api-keys
- Create API key
- Set `OPENAI_API_KEY`

#### 3. Google Gemini (Optional fallback)
- Go to: https://makersuite.google.com/app/apikey
- Create API key
- Set `GOOGLE_API_KEY`

#### 4. OpenRouter (Alternative provider)
- Create an API key in the OpenRouter dashboard
- Set `LLM_PROVIDER=openrouter`
- Set `OPENROUTER_API_KEY`, `OPENROUTER_MODEL_MAIN`, and `OPENROUTER_MODEL_REASONING`
- Keep these backend-only environment variables; do not add them as `VITE_*` variables.

#### 5. Groq (Configured provider)
- Create a Groq API key.
- Set `LLM_PROVIDER=groq`.
- Set `GROQ_API_KEY`, `GROQ_MODEL_MAIN`, and `GROQ_MODEL_REASONING`.
- The currently configured Groq model ID is `openai/gpt-oss-120b`.
- Keep these backend-only environment variables; do not add them as `VITE_*` variables.
- If provider rate-limit or `429` TPM errors occur, do not retry the same live provider call; the provider is enforcing a token-per-minute limit and the application must stop the pipeline cleanly instead of reporting a false success.

#### 5. Brave Search
- Go to: https://api.search.brave.com
- Create account and get API key
- Set `BRAVE_API_KEY`

#### 6. Serper (Alternative search)
- Go to: https://serper.dev
- Create account and get API key
- Set `SERPER_API_KEY`

### Database Configuration

#### PostgreSQL Connection String Format
```
postgresql://user:password@host:port/database
```

For Render PostgreSQL:
- Internal URL (for backend): `postgresql://user:password@internal_render_db.onrender.com/database`
- External URL: Use only for external tools

#### Redis Connection String Format
```
redis://default:password@host:port
```

---

## Database Setup

### Initial Database Migrations

Production uses the checked-in Alembic baseline. From the `backend` directory, run:

```bash
alembic upgrade head
```

Development startup may create tables automatically via SQLAlchemy.

To verify tables created:
```bash
# Connect to PostgreSQL
psql postgresql://user:password@host:port/salesai_db

# List tables
\dt

# Expected tables:
# - lead
# - proposal
# - knowledge_base_entry
# - agent_execution
# - user_activity
```

### Populate Knowledge Base

1. Access the backend API
2. Upload products and services:

```bash
# Upload sample products
curl -X POST https://sales-ai-backend.onrender.com/api/knowledge-base/products/upload \
  -H "Content-Type: application/json" \
  -d @backend/knowledge_base/products.json

# Upload sample services
curl -X POST https://sales-ai-backend.onrender.com/api/knowledge-base/services/upload \
  -H "Content-Type: application/json" \
  -d @backend/knowledge_base/services.json
```

---

## Custom Domain Setup

### Frontend (Vercel)

1. Go to Vercel Project → Settings → Domains
2. Add custom domain
3. Update DNS records:
   - Point `A` record to Vercel IP
   - Or use CNAME to vercel's domain

### Backend (Render)

1. Go to Render Service → Settings → Custom Domain
2. Add domain
3. Update DNS as instructed by Render

### Update CORS

After domains are configured, update backend `CORS_ORIGINS`:
```
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## Monitoring & Logs

### Render Logs
- Backend service → Logs tab
- View real-time application logs
- Search for errors

### Vercel Analytics
- Go to Analytics tab
- Monitor web vitals and performance
- View deployment history

### Health Checks

Backend health endpoint:
```bash
curl https://sales-ai-backend.onrender.com/health
```

Expected response:
```json
{"status": "healthy"}
```

---

## Scaling & Performance

### Backend Scaling (Render)

1. Go to Service Settings → Pricing Plan
2. Upgrade for:
   - More CPU cores
   - More RAM
   - Better performance

### Frontend Optimization (Vercel)

- Automatic optimization with Vercel
- Monitor Core Web Vitals in Analytics
- Consider adding Image Optimization

### Database Scaling (Render)

1. PostgreSQL Settings → Resize
2. Choose larger plan for increased connections/storage
3. No downtime with Render's migration

---

## Backup & Recovery

### Database Backups

Render PostgreSQL includes:
- Daily automated backups
- 7-day retention
- Restore available from dashboard

To manually backup:
```bash
pg_dump postgresql://user:password@host/salesai_db > backup.sql
```

### Redis Backup

For production, consider:
- Enabling persistence (RDB/AOF)
- Regular snapshots to external storage
- Monitoring connection usage

---

## CI/CD Pipeline (Optional GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Trigger Render Deploy
        run: |
          curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }} \
            -H "Content-Type: application/json" \
            -d '{"service_id":"${{ secrets.RENDER_SERVICE_ID }}"}'
      
      - name: Trigger Vercel Deploy
        run: |
          curl -X POST ${{ secrets.VERCEL_DEPLOY_HOOK }} \
            -H "Content-Type: application/json"
```

---

## Troubleshooting

### Backend Won't Deploy

**Error**: Build fails with Python dependencies
- Solution: Ensure `requirements.txt` is in backend root directory
- Check Python version compatibility (3.11 required)

**Error**: Database connection refused
- Solution: Check DATABASE_URL format
- Verify PostgreSQL is in same region
- Wait for health check to pass (5-10 minutes)

### Frontend Build Fails

**Error**: "Module not found"
- Solution: Ensure frontend root is set correctly in Vercel settings
- Check `package.json` exists in frontend directory

**Error**: API calls fail with CORS error
- Solution: Update backend `CORS_ORIGINS` to match frontend URL
- Clear browser cache
- Check network tab in browser devtools

### Performance Issues

**Backend slow responses**
- Check PostgreSQL query performance
- Enable query logging in database settings
- Consider upgrading plan

**Frontend load times**
- Check Vercel Analytics
- Review network tab for slow requests
- Consider enabling Image Optimization

### Redis Connection Issues

**Error**: "WRONGPASS"
- Solution: Check REDIS_URL includes password
- Format: `redis://default:password@host:port`

**Error**: "Connection timeout"
- Solution: Verify Redis is running and accessible
- Check security group/firewall rules
- Verify region consistency

---

## Support

For issues:
1. Check application logs (Render/Vercel dashboards)
2. Verify environment variables are set
3. Test connectivity to services
4. Review GitHub issues and discussions

---

Last Updated: January 2025
