# System Architecture Diagram

This diagram shows the complete system architecture with all components and their interactions.

## Mermaid Diagram

```mermaid
graph TB
    subgraph "External Data Sources"
        CHIRPS[CHIRPS API<br/>Rainfall Data]
        NASA[NASA POWER API<br/>Temperature & Solar]
        ERA5[ERA5 API<br/>Climate Variables]
        NDVI[NDVI API<br/>Vegetation Health]
        OCEAN[Ocean Indices API<br/>ENSO & IOD]
    end

    subgraph "Pipeline Services"
        SCHEDULER[Pipeline Scheduler<br/>APScheduler<br/>Cron: 0 6 * * *]
        ORCHESTRATOR[Pipeline Orchestrator<br/>Execution Coordinator<br/>Lock Management]
        INGESTION[Incremental Ingestion Manager<br/>Date Tracking<br/>180-day Lookback]
        RETRY[Retry Handler<br/>Exponential Backoff<br/>Max 3 Attempts]
        ALERTS[Alert Service<br/>Email SMTP<br/>Slack Webhooks]
        MONITOR[Monitoring Service<br/>Prometheus Metrics<br/>Health Checks]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL Database<br/>Climate Data<br/>Forecasts<br/>Executions)]
        CACHE[Redis Cache<br/>Optional]
    end

    subgraph "Monitoring Stack"
        PROMETHEUS[Prometheus<br/>Metrics Collection<br/>Port: 9091]
        GRAFANA[Grafana<br/>Visualization<br/>Port: 3001]
    end

    subgraph "Outputs"
        FORECASTS[Forecasts<br/>Drought/Flood<br/>Probabilities]
        RECOMMENDATIONS[Recommendations<br/>Crop Advice<br/>Actions]
        TRIGGERS[Insurance Triggers<br/>Payout Decisions]
    end

    SCHEDULER -->|Triggers Daily| ORCHESTRATOR
    ORCHESTRATOR -->|Coordinates| INGESTION
    INGESTION -->|Fetches Incremental| CHIRPS
    INGESTION -->|Fetches Incremental| NASA
    INGESTION -->|Fetches Incremental| ERA5
    INGESTION -->|Fetches Incremental| NDVI
    INGESTION -->|Fetches Incremental| OCEAN
    INGESTION -->|Stores Climate Data| DB
    ORCHESTRATOR -->|Uses on Failure| RETRY
    ORCHESTRATOR -->|Generates| FORECASTS
    FORECASTS -->|Stores| DB
    FORECASTS -->|Creates| RECOMMENDATIONS
    RECOMMENDATIONS -->|Evaluates| TRIGGERS
    ORCHESTRATOR -->|Sends on Failure| ALERTS
    ORCHESTRATOR -->|Records Metrics| MONITOR
    MONITOR -->|Exposes Metrics| PROMETHEUS
    PROMETHEUS -->|Feeds Data| GRAFANA
    DB -->|Queries for Health| MONITOR
    CACHE -.->|Optional Caching| ORCHESTRATOR

    style SCHEDULER fill:#e1f5ff
    style ORCHESTRATOR fill:#fff4e1
    style DB fill:#ffe1e1
    style PROMETHEUS fill:#e1ffe1
    style GRAFANA fill:#e1ffe1
```

## Component Descriptions

### External Data Sources
- **CHIRPS**: Climate Hazards Group InfraRed Precipitation with Station data
- **NASA POWER**: Prediction Of Worldwide Energy Resources
- **ERA5**: ECMWF Reanalysis v5
- **NDVI**: Normalized Difference Vegetation Index
- **Ocean Indices**: El Niño Southern Oscillation (ENSO) and Indian Ocean Dipole (IOD)

### Pipeline Services
- **Scheduler**: Manages automated daily execution at 06:00 UTC
- **Orchestrator**: Coordinates all pipeline stages and handles errors
- **Ingestion Manager**: Tracks last ingestion dates and calculates incremental ranges
- **Retry Handler**: Implements exponential backoff for transient failures
- **Alert Service**: Sends notifications via email and Slack
- **Monitoring Service**: Exposes Prometheus metrics and health checks

### Data Layer
- **PostgreSQL**: Primary data store for climate data, forecasts, and execution metadata
- **Redis**: Optional caching layer for performance optimization

### Monitoring Stack
- **Prometheus**: Collects and stores time-series metrics
- **Grafana**: Provides visualization dashboards

### Outputs
- **Forecasts**: Drought and flood predictions with probabilities
- **Recommendations**: Agricultural advice based on forecasts
- **Triggers**: Insurance payout decisions based on thresholds

## Viewing This Diagram

This Mermaid diagram will render automatically in:
- GitHub/GitLab markdown viewers
- VS Code with Mermaid extension
- Documentation sites (MkDocs, Docusaurus, etc.)
- Mermaid Live Editor: https://mermaid.live/

For ASCII version, see main documentation: `docs/AUTOMATED_PIPELINE_GUIDE.md`
