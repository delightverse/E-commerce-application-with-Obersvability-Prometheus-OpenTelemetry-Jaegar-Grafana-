# E-Commerce Observability Platform

> Implementing OpenTelemetry & Prometheus interoperability for an Ecommerce application

## Project Goal

This project demonstrates production-grade observability using:
- **OpenTelemetry** for distributed tracing, metrics, and logs instrumentation
- **Prometheus** for metrics storage and querying
- **Jaeger** for trace visualization
- **Loki** for log aggregation
- **Grafana** for unified dashboards

**Focus:** OpenTelemetry → Prometheus interoperability using OTLP (OpenTelemetry Protocol)

## Architecture
```
┌──────────────────────────────────────────────────────┐
│                    FastAPI Backend                   │
│         (Instrumented with OpenTelemetry SDK)        │
└────┬────────────────┬──────────────────┬─────────────┘
     │                │                  │
     │ OTLP           │ OTLP             │ stdout/stderr
     │ (traces)       │ (metrics)        │ (logs)
     ↓                ↓                  ↓
┌──────────────────────────────────────────────────────┐
│              OpenTelemetry Collector                 │
│  • Receives all telemetry via OTLP (4317/4318)       │
│  • Processes: sampling, filtering, batching          │
│  • Exports to multiple backends                      │
└───┬──────────────┬──────────────┬────────────────────┘
    │              │              │
    │ OTLP         │ OTLP         │ HTTP
    ↓              ↓              ↓
┌─────────┐  ┌──────────┐  ┌──────────┐
│ Jaeger  │  │Prometheus│  │  Loki    │
│(Traces) │  │(Metrics) │  │ (Logs)   │
└────┬────┘  └────┬─────┘  └────┬─────┘
     │            │             │
     └────────────┴─────────────┴──────────┐
                                           ↓
                                    ┌────────────┐
                                    │  Grafana   │
                                    │(Dashboards)│
                                    └────────────┘
                                    
Additional Component:
┌──────────────────┐
│    Promtail      │ ← Collects Docker container logs
└────────┬─────────┘
         │ HTTP
         ↓
      ┌──────────┐
      │  Loki    │
      └──────────┘
```

**Data Flow Explanation:**

1. **Application Layer**
   - FastAPI sends traces, metrics via OTLP to OTel Collector
   - Application logs go to stdout/stderr (captured by Docker)

2. **Collection Layer**
   - OTel Collector: Central hub for OTLP data
   - Promtail: Scrapes Docker logs from all containers

3. **Storage Layer**
   - Jaeger: Stores and indexes traces
   - Prometheus: Stores time-series metrics (with OTLP receiver enabled)
   - Loki: Stores logs with label-based indexing

4. **Visualization Layer**
   - Grafana: Unified dashboards querying all three backends
   - Correlate traces, metrics, and logs in one place

## Quick Start
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Access services
# - API: http://localhost:8000
# - API Docs (Swagger): http://localhost:8000/docs
# - Prometheus: http://localhost:9090
# - Jaeger UI: http://localhost:16686
# - Loki: http://localhost:3100
# - Grafana: http://localhost:3000 (admin/admin)

# Health checks
curl http://localhost:8000/health
curl http://localhost:9090/-/healthy
curl http://localhost:16686/
curl http://localhost:3100/ready
```

## Observability Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| **FastAPI API** | http://localhost:8000 | Application REST API |
| **FastAPI Docs** | http://localhost:8000/docs | Interactive API documentation |
| **FastAPI Metrics** | http://localhost:8000/metrics | Prometheus metrics endpoint |
| **Prometheus UI** | http://localhost:9090 | Query and explore metrics |
| **Jaeger UI** | http://localhost:16686 | Trace search and visualization |
| **Loki API** | http://localhost:3100 | Log query API (use via Grafana) |
| **Grafana** | http://localhost:3000 | Unified observability dashboards [admin/admin]|
| **OTel Collector Health** | http://localhost:13133 | Collector health endpoint |

