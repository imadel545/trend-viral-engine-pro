# Monitoring Configuration

## 📊 Vue d'ensemble

Ce dossier contient la configuration pour le monitoring de **Trend & Viral Engine Pro**.

## 🛠️ Stack de monitoring

- **Prometheus**: Collecte des métriques
- **Grafana**: Visualisation (dashboards)
- **FastAPI**: Expose les métriques sur `/metrics`

## 🚀 Démarrage

### Avec Docker Compose:

```bash
docker-compose up -d
```

Les services seront disponibles:

- **API**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin par défaut)

### Configuration manuelle:

1. **Démarrer Prometheus**:

```bash
prometheus --config.file=monitoring/prometheus.yml
```

2. **Accéder à Prometheus UI**: http://localhost:9090

## 📈 Métriques disponibles

### Métriques API (FastAPI)

- `api_requests_total`: Nombre total de requêtes
- `api_requests_duration_seconds`: Durée des requêtes
- `api_requests_in_progress`: Requêtes en cours

### Métriques ML

- `viral_score_predictions_total`: Nombre de prédictions
- `viral_score_duration_seconds`: Durée des prédictions
- `model_inference_duration_seconds`: Temps d'inférence

### Métriques Ingestion

- `ingestion_records_total`: Posts collectés par source
- `ingestion_errors_total`: Erreurs de collecte

### Métriques Génération

- `content_generation_total`: Contenus générés
- `content_generation_duration_seconds`: Durée de génération

## 📊 Dashboards Grafana

### Dashboard 1: API Performance

- Request rate (req/s)
- Response time (p50, p95, p99)
- Error rate
- Active connections

### Dashboard 2: ML Pipeline

- Predictions per minute
- Model inference time
- Score distribution
- Model accuracy (online)

### Dashboard 3: Data Ingestion

- Records collected per source
- Collection rate
- Error rate
- Data freshness

### Dashboard 4: System Resources

- CPU usage
- Memory usage
- Disk I/O
- Network traffic

## 🔍 Queries PromQL utiles

### Top 5 endpoints les plus lents:

```promql
topk(5,
  rate(api_requests_duration_seconds_sum[5m])
  /
  rate(api_requests_duration_seconds_count[5m])
)
```

### Taux de prédictions par minute:

```promql
rate(viral_score_predictions_total[1m])
```

### Taux d'erreur API:

```promql
rate(api_requests_total{status=~"5.."}[5m])
/
rate(api_requests_total[5m])
```

## 🚨 Alertes recommandées

### 1. API trop lente

```yaml
- alert: APISlowResponse
  expr: histogram_quantile(0.95, rate(api_requests_duration_seconds_bucket[5m])) > 2
  for: 5m
  annotations:
    summary: "API response time > 2s (p95)"
```

### 2. Taux d'erreur élevé

```yaml
- alert: HighErrorRate
  expr: rate(api_requests_total{status=~"5.."}[5m]) / rate(api_requests_total[5m]) > 0.05
  for: 5m
  annotations:
    summary: "Error rate > 5%"
```

### 3. Modèle trop lent

```yaml
- alert: SlowModelInference
  expr: histogram_quantile(0.95, rate(model_inference_duration_seconds_bucket[5m])) > 1
  for: 5m
  annotations:
    summary: "Model inference > 1s (p95)"
```

## 📝 Notes

- Métriques conservées pendant **15 jours** par défaut
- Scrape interval: **15 secondes**
- Pour production: ajouter Alertmanager pour notifications
- Pour scaling: considérer Thanos ou VictoriaMetrics
