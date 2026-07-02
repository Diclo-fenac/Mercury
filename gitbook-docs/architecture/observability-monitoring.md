# Observability & Monitoring

The Mercury platform provides comprehensive real-time monitoring and alert capability. Observability is integrated into the core orchestrators, generating structured Prometheus metrics that are visualized on pre-provisioned Grafana dashboards.

---

## 1. Metrics Instrumentation

Application metrics are managed in [`app/utils/metrics.py`](file:///home/mium/code/mercury/app/utils/metrics.py) using the Prometheus Python client. 

### Search Metrics
* **`mercury_search_total` (Counter):** Tracks overall search volume. Labeled by `query_type` (e.g., `keyword`, `semantic`, `hybrid`) and `result_count` (number of matches returned).
* **`mercury_search_latency_seconds` (Histogram):** Records execution time for query processing. Labeled by `search_type`.
* **`mercury_zero_result_queries_total` (Counter):** Tracks how often a search returns no items. Labeled by `search_type` and `fallback_used` (indicating if semantic query expansion was triggered).

### Caching Metrics
* **`mercury_cache_hits_total` (Counter):** Total hits on Redis search keys.
* **`mercury_cache_misses_total` (Counter):** Total misses requiring backend queries.
* **`mercury_cache_hit_rate` (Gauge):** Percentage of queries resolved via the cache (value between `0` and `1`).

### LLM & Vision Metrics
* **`mercury_llm_requests_total` (Counter):** Volumetric tracker for Gemini API prompts.
* **`mercury_llm_latency_seconds` (Histogram):** Tracks round-trip latency of Gemini content generation.
* **`mercury_image_search_total` (Counter):** Volumetric tracker for vision-based uploads.

### System Load Metrics
* **`mercury_active_requests` (Gauge):** Tracks current concurrent HTTP/WebSocket requests.
* **`mercury_concurrent_users` (Gauge):** Estimated volume of concurrent active sessions.

---

## 2. Scraping Infrastructure

Prometheus is configured via [`prometheus.yml`](file:///home/mium/code/mercury/infra/prometheus/prometheus.yml) to scrape the metrics endpoint exposed by the FastAPI server:

```yaml
global:
  scrape_interval: 10s
  evaluation_interval: 10s

scrape_configs:
  - job_name: "mercury-assistant"
    metrics_path: "/api/v1/health/metrics"
    static_configs:
      - targets: ["app:8000"]
```

---

## 3. Provisioned Grafana Dashboard

The Grafana service is pre-provisioned to automatically load data sources and dashboards on startup, ensuring a "zero-setup" visualization environment.

* **Configuration Provider:** [`infra/grafana/provisioning/dashboards/dashboard.yaml`](file:///home/mium/code/mercury/infra/grafana/provisioning/dashboards/dashboard.yaml) directs Grafana to read JSON layouts from `/etc/grafana/provisioning/dashboards`.
* **Dashboard Layout:** [`mercury_dashboard.json`](file:///home/mium/code/mercury/infra/grafana/provisioning/dashboards/mercury_dashboard.json) defines a multi-panel dashboard:

### Grafana Panel Breakdown

| Panel Title | Type | Metric Expression | Description |
| :--- | :--- | :--- | :--- |
| **Estimated Concurrent Users** | Stat | `mercury_concurrent_users` | Active user sessions. |
| **Active API Requests** | Stat | `mercury_active_requests` | Live HTTP request loops. |
| **Search Cache Hit Rate** | Gauge | `mercury_cache_hit_rate * 100` | Percentage of search queries resolved in cache. |
| **Zero Result Query Count** | Stat | `sum(mercury_zero_result_queries_total)` | Volume of search terms returning empty. |
| **Search Request Volume** | Timeseries | `sum(rate(mercury_search_total[1m])) by (query_type)` | Searches per second, grouped by type. |
| **Search Response Latency** | Timeseries | `histogram_quantile(0.95, ...)` & `0.50` | p95 and p50 response latency in seconds. |
| **Cache Performance Counters** | Timeseries | `rate(mercury_cache_hits_total[1m])` & `misses` | Traffic hit/miss comparison rate. |
| **Gemini LLM Request Latency** | Timeseries | `histogram_quantile(0.90, ...)` | p90 response time of the Gemini LLM engine. |
| **Image Search Volume** | Timeseries | `sum(rate(mercury_image_search_total[1m]))` | Uploaded image queries per second. |
