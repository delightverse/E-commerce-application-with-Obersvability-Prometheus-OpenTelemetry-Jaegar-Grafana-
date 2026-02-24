# E-Commerce Observability Platform

> Implementing OpenTelemetry & Prometheus interoperability for an Ecommerce application

##  Project Goal

This project demonstrates production-grade observability using:
- **OpenTelemetry** for distributed tracing and metrics instrumentation
- **Prometheus** for metrics storage and querying
- **Jaeger** for trace visualization
- **Grafana** for unified dashboards

**Focus:** OpenTelemetry → Prometheus interoperability using OTLP (OpenTelemetry Protocol)

## Architecture
```
┌─────────────┐
│   FastAPI   │ ← Application instrumented with OpenTelemetry
└──────┬──────┘
       │ OTLP (traces + metrics)
       ↓
┌──────────────────┐
│ OTel Collector   │ ← Receives, processes, exports observability data
└─────┬────────┬───┘
      │        │
      │        └─────→ Prometheus (metrics via OTLP)
      │
      └──────────────→ Jaeger (traces via OTLP)
                  ↓
            ┌──────────┐
            │ Grafana  │ ← Unified visualization
            └──────────┘
```
## Quick Start
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Access services
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Prometheus: http://localhost:9090
# - Jaeger: http://localhost:16686
# - Grafana: http://localhost:3000 (admin/admin)
```