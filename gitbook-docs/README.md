# Introduction

Welcome to the **Mercury AI Assistant & Search Engine** documentation. This GitBook-compatible reference guide explains the architecture, design decisions, implementation details, and deployment workflows for the Mercury system.

## Project Overview

Mercury is a high-performance, multi-tenant AI shopping assistant and advanced search platform. It is engineered using a clean, layered architecture to provide:
- **Hybrid Search Engine:** Combines fast fuzzy keyword matching with deep semantic vector search.
- **AI Shopping Assistant:** Integrates LLM reasoning via Google Gemini, equipped with custom toolsets for personalized search, variant matching, and multi-turn chat.
- **Production-Ready Observability:** Includes metrics endpoints scraping for Prometheus and visualization in Grafana.
- **Streamlined Containerization:** Leverages multi-stage Docker builds to reduce runtime container image size by over 80% (from 2.8GB to ~500MB).
- **High-Performance Caching:** Minimizes database traffic by caching frequent search results using an asynchronous Redis connection pool, delivering sub-50ms latency on hot query paths.

## Document Map

To understand the codebase in detail, navigate through the following sections:

- **[System Architecture](architecture/clean-architecture.md):** A deep dive into the 6-layer Clean Architecture layout and dependency injection.
- **[Advanced Search Engine](architecture/search-system.md):** Lexical and semantic search, Reciprocal Rank Fusion (RRF), variant matching, and product boosting.
- **[Caching & Performance](architecture/caching-performance.md):** Redis async caching layer, connection pool settings, and database traffic mitigation.
- **[Infrastructure & Deployment](architecture/infrastructure-deployment.md):** Docker multi-stage optimization, CPU/GPU dependency splitting, and setup scripts.
- **[Observability & Monitoring](architecture/observability-monitoring.md):** Prometheus instrumentation metrics and pre-configured Grafana dashboards.
- **[API Reference](api-reference/endpoints.md):** API router paths, endpoints for search, chat, images, and WebSocket handlers.
