# Getting Started with Trend & Viral Engine Pro

## Quick Start Guide

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- 8GB RAM minimum
- 20GB disk space

### Installation

1. **Clone and setup**

```bash
cd "Trend & Viral Engine Pro"
cp .env.example .env
```

2. **Configure API keys**

Edit `.env` and add your API keys:

```bash
GROQ_API_KEY=gsk_your_key_here
TIKTOK_API_KEY=your_tiktok_key
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
```

3. **Start with Docker**

```bash
docker-compose up -d
```

4. **Or run locally**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

### First Steps

1. **Check API health**

```bash
curl http://localhost:8000/health
```

2. **Trigger data ingestion**

```bash
curl -X POST http://localhost:8000/api/v1/admin/trigger-ingestion
```

3. **Get top trends**

```bash
curl "http://localhost:8000/api/v1/trends/topK?k=10&country=FR"
```

4. **Generate content**

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI automation 2026", "duration": 25}'
```

## Access Dashboards

- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **MLflow**: http://localhost:5000
- **Prometheus**: http://localhost:9090

## Next Steps

- Read [Architecture](architecture.md) for system design
- Check [API Reference](api-reference.md) for all endpoints
- See [Development Guide](development.md) for contributing
