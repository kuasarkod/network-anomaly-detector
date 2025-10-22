# Advanced Network Anomaly Detector

Modular, real-time security pipeline that ingests network telemetry and log streams, enriches them with contextual data, and surfaces anomalies through alerts, metrics, and dashboards.

## 🚀 Highlights

- **Multi-source collectors** for syslog, NetFlow, and file-based ingestion.
- **Streaming anomaly engine** combining heuristic detectors with machine-learning models (e.g., isolation forest, port-scan heuristics).
- **Flexible messaging backbone** supporting Redis Streams and Kafka to decouple producers and processing.
- **Normalization → enrichment → detection → alerting** pipeline with pluggable enrichers (GeoIP/ASN) and alert dispatchers.
- **Alerting adapters** for Slack webhooks, SMTP e-mail, and extensible dispatch logic.
- **Observability baked-in** via Prometheus metrics and Grafana dashboards.
- **FastAPI REST API** exposing CRUD endpoints, SSE feeds, and a CLI companion for scripting.
- **Docker-first developer experience** with Compose orchestration, monitoring stack, and lint/test tooling.

## 📁 Repository Layout

```
network-anomaly-detector/
├── config/                # Shared configuration and .env templates
├── docker/                # Helper files for Docker-based deployments
├── docs/                  # Architecture notes and deployment guides
├── src/
│   └── anomaly_detector/
│       ├── api/           # FastAPI application and routing
│       ├── alerts/        # Slack / SMTP dispatchers
│       ├── collectors/    # Syslog, NetFlow, file collectors
│       ├── pipeline/      # Normalization, enrichment, detection stages
│       ├── models/        # ML wrappers and scoring utilities
│       └── storage/       # Persistence layer abstractions
├── tests/                 # Pytest suite (metrics, pipeline, utils)
├── web/                   # React dashboard (Vite + TypeScript)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## ⚙️ Local Setup

> The project is managed with `Poetry`. Install it following the [official instructions](https://python-poetry.org/docs/#installation) if it is not already available.

```bash
# Install dependencies
poetry install

# Activate the virtual environment
poetry shell

# Copy and edit environment variables
cp config/.env.example config/.env
```

## 🧪 Tests & Code Quality

```bash
# Run unit tests
poetry run pytest

# Lint and format checks
poetry run ruff check .
poetry run black --check .
poetry run mypy src/anomaly_detector

# Install pre-commit hooks
poetry run pre-commit install
```

## 🐳 Running with Docker

```bash
# Start the full stack
docker compose up --build

# Health check
curl http://localhost:8080/health

# List recent anomalies
curl http://localhost:8080/anomalies?limit=10

# Fetch Prometheus metrics
curl http://localhost:8080/metrics
```

Services exposed by Compose:
- **API**: `http://localhost:8080`
- **Dashboard**: `http://localhost:5173`
- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000` (default credentials `admin` / `admin`)

The dashboard consumes the REST API and SSE feeds automatically. To point it to a different hostname or port, update `CORS_ORIGINS` in `config/.env` and `VITE_API_BASE` in `docker-compose.yml`.

## 🧭 CLI Usage

```bash
# Ingest a JSON array of events
poetry run python -m anomaly_detector.cli ingest samples/events.json

# Inspect in-memory anomalies
poetry run python -m anomaly_detector.cli stats
```

## 📊 Web Dashboard

- **Endpoint**: `http://localhost:5173`
- **API base URL**: `VITE_API_BASE` (defaults to `http://api:8080` inside Docker)
- **Data sources**: `/anomalies` REST endpoint + `/events` Server-Sent Events stream
- **Local development**: from `web/dashboard`, run `npm install` and `npm run dev`

## 📈 Observability & Metrics

- Prometheus-compatible metrics are exposed at `/metrics`, and the bundled Prometheus instance scrapes the API service by default.
- `anomaly_detector_events_total` (counter) and `anomaly_detector_last_score` (gauge) are updated by the processing pipeline.
- `tests/test_metrics.py` provides coverage for metric instrumentation.

## 🗺 Roadmap (MVP)

1. Expand collector adapters (Syslog, NetFlow, file tailing)
2. Harden Redis/Kafka queue integration
3. Extend streaming anomaly models (IsolationForest + HalfSpaceTrees)
4. Broaden alert channels (Slack, Telegram, email)
5. Polish REST API/CLI and enrich Prometheus metrics
6. Iterate on the React-based operations dashboard

See `docs/` for detailed architectural notes and deployment runbooks.

## 🤝 Contributing

- Install `pre-commit` hooks and format code before submitting patches.
- Review existing issues and discussions before opening new ones.
- Update roadmap entries under `docs/` when proposing significant features.

## 📄 License

The project is intended to ship under the MIT License. A formal `LICENSE` file will be added in an upcoming revision.
