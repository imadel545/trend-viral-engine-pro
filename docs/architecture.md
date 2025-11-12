# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources                              │
│  TikTok Creative Center │ Google Trends │ Reddit             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              IngestionService (Every 10 min)                  │
│  - Collects trending topics, hashtags, sounds                │
│  - Stores raw data in Parquet format                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              FeatureService                                   │
│  - Temporal features (slope, acceleration)                    │
│  - Text embeddings (Sentence Transformers)                    │
│  - Vision embeddings (CLIP)                                   │
│  - Audio embeddings (VGGish)                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              ScoringService                                   │
│  - LightGBM baseline model                                    │
│  - Isotonic calibration                                       │
│  - Outputs: p_breakout_24h, predicted_views                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              SelectionService                                 │
│  - Top K selection                                            │
│  - Diversity optimization                                     │
│  - Epsilon-greedy exploration                                 │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              GeneratorService                                 │
│  - Script generation (Groq LLM)                               │
│  - Video generation (MoviePy)                                 │
│  - Caption generation                                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Content Output                                   │
│  - video.mp4                                                  │
│  - caption.txt                                                │
│  - metadata.json                                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ (Manual publication)
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              FeedbackService                                  │
│  - Collects metrics (views, likes, watch time)                │
│  - Generates training labels                                  │
│  - Triggers retraining when threshold met                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Model Training                                   │
│  - LightGBM retraining                                        │
│  - Logs to MLflow                                             │
│  - Updates production model                                   │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. IngestionService
- **Frequency**: Every 10 minutes
- **Sources**: TikTok, Google Trends, Reddit
- **Output**: Raw Parquet files in `data/raw/`
- **Error Handling**: Exponential backoff, retry logic

### 2. FeatureService
- **Features Extracted**:
  - Temporal: slope, acceleration, hour, day_of_week
  - Text: Multilingual embeddings (384 dim)
  - Vision: CLIP embeddings (for thumbnails)
  - Audio: VGGish embeddings (for sounds)
- **Output**: Feature tables in `data/features/`

### 3. ScoringService
- **Model**: LightGBM (500 trees, early stopping)
- **Calibration**: Isotonic regression
- **Metrics**: AUC ≥ 0.80 target
- **Predictions**:
  - `p_breakout_24h`: Probability of going viral (0-1)
  - `predicted_views_24h`: Estimated views in 24h

### 4. SelectionService
- **Strategies**:
  - TopK: Pure score-based selection
  - Diversity: Balance between score and variety
  - Exploration: Epsilon-greedy (10% random)
- **Default**: Diversity strategy (70% exploitation, 30% diversity)

### 5. GeneratorService
- **Script Generation**:
  - LLM: Groq API (GPT-OSS 120B)
  - Structure: Hook + Payoff + CTA
  - Output: JSON with hook, payoff, cta, caption
- **Video Generation**:
  - Engine: MoviePy + FFmpeg
  - Format: MP4, 1080x1920, 30fps
  - Duration: 20-30 seconds
  - Layers: Background + Text overlays

### 6. FeedbackService
- **Metrics Collected**:
  - Views, Likes, Comments, Shares
  - Watch time ratio
  - Engagement rate
- **Retraining Trigger**: ≥ 100 new samples
- **Label Generation**: `is_breakout` based on quantiles

## Data Flow

1. **Ingestion** (10 min cycle)
   - Fetch data from sources
   - Store in `data/raw/*.parquet`

2. **Feature Extraction** (15 min cycle)
   - Load raw data
   - Extract features
   - Store in `data/features/*.parquet`

3. **Scoring** (on-demand)
   - Load features
   - Score with model
   - Cache results

4. **Selection** (3x daily)
   - Load scored data
   - Apply selection strategy
   - Queue for generation

5. **Generation** (3x daily)
   - Generate script (via Groq)
   - Create video (via MoviePy)
   - Save content + metadata

6. **Feedback** (manual submission)
   - Submit metrics via API
   - Store in `data/feedback/`
   - Check retrain threshold

7. **Retraining** (nightly if triggered)
   - Generate labels
   - Train new model
   - Log to MLflow
   - Update production

## Storage Structure

```
data/
├── raw/              # Raw ingested data
│   ├── google_trends_*.parquet
│   ├── reddit_*.parquet
│   └── tiktok_*.parquet
├── features/         # Extracted features
│   └── features_*.parquet
├── labels/           # Training labels
│   └── labels_*.parquet
└── feedback/         # Performance metrics
    └── feedback_*.json

models/              # Trained models
└── baseline_model.pkl

outputs/             # Generated content
├── video_*.mp4
├── video_*.txt      # Captions
└── video_*.json     # Metadata

mlruns/              # MLflow experiments
└── 0/
    └── runs/

logs/                # Application logs
├── trend-engine-*.log
└── errors-*.log
```

## Scaling Considerations

### Current Capacity
- **Ingestion**: 1,000 topics/hour
- **Scoring**: < 200ms per request (P95)
- **Generation**: 3 videos/day

### Future Scaling
- Horizontal scaling via Kubernetes
- Distributed training with Ray
- Message queue (RabbitMQ/Kafka) for async processing
- CDN for content delivery
