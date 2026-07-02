"""
Prometheus metrics for Mercury AI Assistant
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# Search metrics
SEARCH_TOTAL = Counter(
    'mercury_search_total',
    'Total search requests',
    ['query_type', 'result_count']
)

SEARCH_LATENCY = Histogram(
    'mercury_search_latency_seconds',
    'Search request latency',
    ['search_type']
)

ZERO_RESULT_QUERIES = Counter(
    'mercury_zero_result_queries_total',
    'Total queries returning zero results',
    ['search_type', 'fallback_used']
)

# Cache metrics
CACHE_HITS = Counter('mercury_cache_hits_total', 'Total cache hits')
CACHE_MISSES = Counter('mercury_cache_misses_total', 'Total cache misses')
CACHE_HIT_RATE = Gauge('mercury_cache_hit_rate', 'Current cache hit rate (0-1)')

# Image search metrics
IMAGE_SEARCH_TOTAL = Counter(
    'mercury_image_search_total',
    'Total image search requests',
    ['result_count']
)

IMAGE_SEARCH_ACCURACY = Histogram(
    'mercury_image_search_accuracy',
    'Image retrieval accuracy (Top-K match)'
)

# LLM metrics
LLM_REQUESTS = Counter('mercury_llm_requests_total', 'Total LLM requests')
LLM_LATENCY = Histogram('mercury_llm_latency_seconds', 'LLM request latency')

# Concurrency metrics
ACTIVE_REQUESTS = Gauge('mercury_active_requests', 'Currently active requests')
CONCURRENT_USERS = Gauge('mercury_concurrent_users', 'Estimated concurrent users')

# Product metrics
PRODUCT_FETCH_TOTAL = Counter('mercury_product_fetch_total', 'Total product fetches')


def metrics_endpoint():
    """Prometheus /metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)