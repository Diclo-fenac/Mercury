"""
Prometheus Metrics - Layer 6: Infrastructure
FastAPI instrumentation and custom metrics
"""
from prometheus_client import Counter, Histogram

# Standard Counters
SEARCH_REQUESTS = Counter(
    'mercury_search_requests_total',
    'Total search requests',
    ['tenant_id', 'search_type']
)

RECOMMENDATION_REQUESTS = Counter(
    'mercury_recommendation_requests_total',
    'Total recommendation requests',
    ['tenant_id', 'strategy']
)

# Histograms
SEARCH_LATENCY = Histogram(
    'mercury_search_latency_seconds',
    'Search latency in seconds',
    ['tenant_id', 'search_type']
)

def setup_metrics(app):
    """Integrate prometheus metrics into FastAPI app"""
    # Assuming prometheus-fastapi-instrumentator is used,
    # or expose a /metrics endpoint directly
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    except ImportError:
        pass
