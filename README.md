# Sales AI - AI-Powered Lead Qualification & Proposal Generation

A full-stack application foundation that uses AI agents to qualify sales leads, analyze requirements, and generate knowledge-base-grounded proposal drafts. Local Docker development is supported; production deployment requires provider keys and Render/Vercel setup.

## Features

✨ **Intelligent Lead Qualification**
- Automated lead analysis using LangGraph agents
- Explainable scoring with Fit, Readiness, Opportunity, and Risk metrics
- Composite scores (0-100) with detailed reasoning

🔍 **Comprehensive Research**
- Automatic company research and background analysis
- Industry vertical and market position assessment
- Recent news and public information gathering

📋 **Requirements Analysis**
- Functional and non-functional requirement extraction
- Missing information identification
- Assumption documentation and priority mapping

💡 **Solution Matching**
- AI-powered product/service matching from knowledge base
- Coverage percentage analysis
- Gap identification and workarounds

📄 **Proposal Generation**
- Automated proposal creation with executive summary
- Implementation roadmap and timeline
- Pricing and success metrics
- Professional formatting ready for delivery

✅ **Quality Review**
- Automated proposal validation
- Claim verification against requirements
- Risk assessment and escalation paths
- Follow-up question generation

## Tech Stack

### Backend
- **FastAPI 0.104.1** - Modern Python web framework with async support
- **LangGraph 0.2.28** - Agent orchestration and workflow management
- **LangChain 0.2.x** - LLM abstractions and tool integration
- **Anthropic Claude 3** - Primary LLM, with OpenAI and Google provider selection
- **ChromaDB 0.4.17** - Vector database for RAG knowledge base
- **PostgreSQL 15** - Persistent data storage
- **Redis 7** - Caching and performance optimization
- **SQLAlchemy 2.0.23** - ORM and database migrations
- **Pydantic 2.5.0** - Data validation and serialization
- **Docker** - Containerization and deployment

### Current implementation notes
- Qualification thresholds and score weights are configurable with environment variables such as `QUALIFIED_SCORE_THRESHOLD` and `FIT_SCORE_WEIGHT`.
- Web search results use Redis caching when Redis is available, with an in-memory development fallback.
- PDF and DOCX inquiries can be uploaded through `POST /api/leads/upload` and the New Lead form.
- Solution matches are checked against the knowledge base before proposal generation; unsupported matches are rejected.
- No production URLs are included in this repository yet. Follow [DEPLOYMENT.md](./DEPLOYMENT.md) to deploy.

### Frontend
- **React 18.2.0** - UI framework
- **TypeScript 5.2.2** - Type-safe development
- **Vite 5.0.0** - Fast build tooling
- **Tailwind CSS 3.3.0** - Utility-first styling
- **Axios** - HTTP client
- **React Router** - Client-side routing

### Infrastructure
- **Render** - Backend hosting with PostgreSQL and Redis
- **Vercel** - Frontend hosting with CDN
- **GitHub Actions** - CI/CD pipeline (optional)

## Architecture

```
Sales AI Application
├── Backend (FastAPI)
│   ├── Services Layer
│   │   ├── LLM Service (Anthropic/OpenAI/Google)
│   │   ├── RAG Service (ChromaDB vector search)
│   │   ├── Web Search (Brave/Serper)
│   │   ├── Document Processing (PDF/DOCX)
│   │   └── Cache Service (Redis)
│   ├── Agents Layer (LangGraph Orchestration)
│   │   ├── Research Agent
│   │   ├── Requirements Agent
│   │   ├── Qualification Agent
│   │   ├── Solution Matching Agent
│   │   ├── Proposal Agent
│   │   └── Reviewer Agent
│   ├── API Layer (REST endpoints)
│   └── Database Layer (SQLAlchemy/PostgreSQL)
└── Frontend (React + TypeScript)
    ├── Pages (InputForm, Dashboard, LeadsList)
    ├── Components (Card views for each agent)
    ├── Hooks (API integration, state management)
    └── Styling (Tailwind CSS)
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+
- Python 3.11+
- Git

### Local Development

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd sales-ai
```

2. **Create environment file**
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

3. **Start services with Docker Compose**
```bash
docker-compose up
```

This starts:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- Backend API (port 8000)
- Frontend dev server (port 5173)

4. **Access the application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup (Without Docker)

1. **Backend setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run the server
uvicorn app.main:app --reload
```

2. **Frontend setup**
```bash
cd frontend
npm install
npm run dev
```

### Provider-backed E2E test

The real-provider test is opt-in. For development, use Gemini with a Google AI Studio API key:

```bash
cd backend
cp .env.example .env
# Set GOOGLE_API_KEY in backend/.env, then run:
RUN_LLM_E2E=1 .venv/bin/python -m pytest tests/test_provider_e2e.py::test_provider_backed_pipeline_end_to_end -q
```

Set `LLM_PROVIDER=groq` and use Groq with `GROQ_API_KEY`, `GROQ_MODEL_MAIN`, and `GROQ_MODEL_REASONING` in `backend/.env`. The current configured Groq model ID is `openai/gpt-oss-120b`. To use Gemini instead, set `LLM_PROVIDER=gemini` and provide `GOOGLE_API_KEY`; to use OpenRouter instead, set `LLM_PROVIDER=openrouter` plus `OPENROUTER_API_KEY`, `OPENROUTER_MODEL_MAIN`, and `OPENROUTER_MODEL_REASONING`. Model IDs are passed through to the provider’s OpenAI-compatible API. Never commit `backend/.env` or print API keys in command output. The mock-provider test remains available for offline validation. Do not run a real E2E repeatedly when a provider reports a quota or TPM rate limit; a live provider failure such as Groq `429 rate_limit_exceeded` is an external provider limitation, not an application success.

Set `LLM_FALLBACK_PROVIDERS=groq` to automatically use a configured Groq provider when the selected provider reports quota exhaustion. Fallback occurs only for quota responses; it does not hide authentication, validation, or ordinary provider errors.

## Configuration

### Environment Variables

Create `backend/.env` with required variables:

```env
# LLM Provider (gemini, groq, openrouter, anthropic, openai, google)
LLM_PROVIDER=groq
LLM_MODEL_MAIN=gemini-3.6-flash
LLM_MODEL_REASONING=gemini-3.6-flash

# Required only when LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL_MAIN=provider/model-id
OPENROUTER_MODEL_REASONING=provider/model-id

# Required only when LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_google_ai_studio_key

# API Keys
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
GROQ_API_KEY=your_groq_key

# Required only when LLM_PROVIDER=groq
GROQ_MODEL_MAIN=openai/gpt-oss-120b
GROQ_MODEL_REASONING=openai/gpt-oss-120b

# Search APIs
BRAVE_API_KEY=your_key
SERPER_API_KEY=your_key

# Database
POSTGRES_USER=salesai
POSTGRES_PASSWORD=your_database_password
POSTGRES_DB=salesai_db
DATABASE_URL=postgresql://salesai:your_database_password@localhost:5432/salesai_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
API_AUTH_TOKEN=your_local_api_token

# Knowledge Base
KNOWLEDGE_BASE_PATH=./knowledge_base
```

Protected write endpoints require `Authorization: Bearer <API_AUTH_TOKEN>`. Health and provider-readiness endpoints remain public. Configure rate limits and timeout values through the environment variables shown in `backend/.env.example`.

For production database setup, run migrations from `backend` before starting the service:

```bash
alembic upgrade head
```

Development startup may create tables automatically; production startup requires the migration step.

### Knowledge Base Setup

The system uses a RAG (Retrieval Augmented Generation) approach. Add products and services:

1. **Create knowledge base JSON files**
```bash
backend/knowledge_base/
├── products.json
└── services.json
```

2. **Upload via API**
```bash
curl -X POST http://localhost:8000/api/knowledge-base/products/upload \
  -H "Content-Type: application/json" \
  -d @backend/knowledge_base/products.json
```

See [Knowledge Base Format](./backend/knowledge_base/README.md) for structure.

## API Endpoints

### Lead Management

**Submit a lead for qualification**
```
POST /api/leads
Content-Type: application/json

{
  "company_name": "Acme Corp",
  "inquiry_text": "We need AI-powered customer service automation...",
  "industry": "Healthcare",
  "company_size": "500-1000",
  "budget": "$500K-$1M",
  "timeline": "3 months",
  "additional_context": "Priority for Q1 2025"
}

Response: { "lead_id": "uuid" }
```

**Get lead status and results**
```
GET /api/leads/{lead_id}

Response: {
  "id": "uuid",
  "lead_status": "Qualified",
  "composite_score": 78,
  "result": {
    "research": {...},
    "requirements": {...},
    "qualification": {...},
    "solution_matching": {...},
    "proposal": {...},
    "reviewer": {...}
  }
}
```

**List all leads**
```
GET /api/leads?skip=0&limit=20&status=Qualified

Response: { "leads": [...], "total": 42 }
```

### Proposal Management

**Get proposal for a lead**
```
GET /api/proposals/{lead_id}

Response: { "proposal": {...}, "lead_id": "uuid" }
```

**Approve proposal**
```
POST /api/proposals/{lead_id}/approve
Content-Type: application/json

{ "approved_by": "sales.manager@company.com" }
```

**Send proposal to customer**
```
POST /api/proposals/{lead_id}/send
Content-Type: application/json

{ "recipient_email": "customer@acme.com" }
```

### Knowledge Base

**Search products**
```
GET /api/knowledge-base/products/search?query=AI%20automation&limit=5
```

**Upload products**
```
POST /api/knowledge-base/products/upload
Content-Type: application/json

[
  {
    "name": "ProductName",
    "description": "...",
    "features": [...],
    "pricing": "$X - $Y",
    "implementation_timeline": "2-4 weeks"
  }
]
```

Full API documentation available at `http://localhost:8000/docs`

## Usage Workflow

### 1. Submit Lead
Customer submits inquiry through the web form with:
- Company information
- Business requirements
- Budget and timeline
- Additional context

### 2. Automatic Analysis
Backend orchestrates 7-agent pipeline:
1. **Research Agent** - Gathers company background
2. **Requirements Agent** - Extracts structured needs
3. **Qualification Agent** - Scores lead (0-100)
4. **Solution Agent** - Matches products/services
5. **Proposal Agent** - Generates proposal
6. **Reviewer Agent** - Quality validation
7. **Completion** - Results ready

### 3. View Results
Dashboard displays:
- Lead qualification score with breakdown
- Research findings
- Extracted requirements
- Recommended solutions with coverage
- Generated proposal
- Quality review and next steps

### 4. Manage Proposal
- Review proposal content
- Approve for sending
- Send to customer
- Track status

## Deployment

For production deployment to Render (backend) and Vercel (frontend), see [DEPLOYMENT.md](./DEPLOYMENT.md)

Quick deploy:
1. Push to GitHub main branch
2. Render automatically deploys backend
3. Vercel automatically deploys frontend
4. Configure environment variables in each platform
5. Update CORS settings with production URLs

## Performance Optimization

### Caching
- Web search results cached for 24 hours
- Knowledge base queries cached with TTL
- Redis for distributed caching

### Database Indexing
- Composite index on (lead_id, created_at)
- Index on lead_status for filtering
- Index on pipeline_result for searches

### Frontend Optimization
- Code splitting with Vite
- Image lazy loading
- CSS minification
- Component memoization for performance

## Monitoring

### Backend Monitoring
- Application Insights (optional)
- Render metrics and logs
- PostgreSQL query monitoring

### Frontend Monitoring
- Vercel Analytics
- Core Web Vitals
- Error tracking (Sentry optional)

## Development

### Project Structure
```
sales-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py              # Configuration
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── schemas.py             # Pydantic schemas
│   │   ├── database.py            # DB setup
│   │   ├── services/              # Business logic
│   │   ├── agents/                # AI agents
│   │   └── api/                   # REST routes
│   ├── requirements.txt
│   ├── Dockerfile
│   └── knowledge_base/
├── frontend/
│   ├── src/
│   │   ├── App.tsx                # Main app
│   │   ├── components/            # React components
│   │   ├── hooks/                 # Custom hooks
│   │   ├── types/                 # TypeScript types
│   │   └── index.tsx              # Entry point
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── DEPLOYMENT.md
└── README.md
```

### Adding New Agents

1. Create `backend/app/agents/your_agent.py`
2. Implement agent function with proper prompting
3. Register in `backend/app/agents/orchestrator.py`
4. Add corresponding Pydantic schema
5. Create frontend component for visualization

### Adding to Knowledge Base

1. Add products/services to JSON files
2. Upload via API endpoint
3. Verify with search endpoint
4. Test in proposal generation

## Troubleshooting

### Backend Issues

**LLM API Errors**
- Check API key format and validity
- Verify rate limits not exceeded
- Check model name spelling
- Review LLM provider documentation

**Database Connection**
- Verify PostgreSQL running
- Check DATABASE_URL format
- Confirm database exists
- Check user permissions

**Redis Connection**
- Verify Redis running
- Check REDIS_URL format
- Verify Redis password (if required)
- Check port availability

### Frontend Issues

**API Connection Errors**
- Verify backend running on correct port
- Check CORS configuration
- Clear browser cache
- Check network tab in devtools

**Build Errors**
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (require 18+)
- Verify Tailwind configuration

## Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## License

MIT License - see LICENSE file for details

## Support

- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Email: support@example.com

## Roadmap

- [ ] Multi-language support
- [ ] Webhook integrations for CRM systems
- [ ] Advanced analytics dashboard
- [ ] Custom agent templates
- [ ] Mobile app
- [ ] Voice-to-text inquiry input
- [ ] PDF export with custom branding
- [ ] A/B testing for proposal variations

## Changelog

### v1.0.0 (January 2025)
- Initial release
- 7-agent orchestration pipeline
- Full lead qualification workflow
- Proposal generation
- React frontend with TypeScript
- Docker Compose local development
- Production deployment guides

---

**Built with ❤️ using FastAPI, LangGraph, and React**

Last Updated: January 2025
