#!/bin/bash

# Start script for Trend & Viral Engine Pro

set -e

echo "🚀 Starting Trend & Viral Engine Pro..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env with your API keys before continuing."
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/raw data/features data/labels data/feedback
mkdir -p models outputs logs
mkdir -p mlruns

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo "🏥 Checking service health..."
curl -f http://localhost:8000/health || {
    echo "❌ API health check failed"
    docker-compose logs api
    exit 1
}

echo "✅ All services are up and running!"
echo ""
echo "📊 Access points:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Grafana: http://localhost:3000 (admin/admin)"
echo "   - MLflow: http://localhost:5000"
echo "   - Prometheus: http://localhost:9090"
echo ""
echo "🎯 Next steps:"
echo "   1. Trigger ingestion: curl -X POST http://localhost:8000/api/v1/admin/trigger-ingestion"
echo "   2. Check trends: curl http://localhost:8000/api/v1/trends/topK?k=10"
echo "   3. Generate content: See docs/getting-started.md"
echo ""
echo "📝 View logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"
