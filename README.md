# Mercury AI Assistant

[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Typesense](https://img.shields.io/badge/Typesense-29.0-D63533.svg?style=flat&logo=typesense&logoColor=white)](https://typesense.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-BUSL--1.1-blue.svg)](LICENSE)

Mercury is an enterprise-grade, multi-tenant AI search and recommendation engine designed for e-commerce. Built with **FastAPI**, **Typesense**, **PostgreSQL**, **Redis**, and **Google Gemini**, it delivers sub-50ms hybrid search, AI-powered conversational shopping assistance, and a plug-and-play storefront search widget.

---

## Key Features

- ⚡ **Sub-50ms Latency**: Hybrid keyword (BM25) and vector search powered by Typesense.
- 🏢 **Native Multi-Tenancy**: Organization-isolated catalogs, search indices, and merchandising rules.
- 🤖 **AI RAG Assistant**: Grounded product recommendations and conversational Q&A (`full` mode).
- 🎨 **Drop-in Web Widget**: Zero-dependency UI widget ready to embed on any e-commerce storefront.
- 🎯 **Merchandising Engine**: Pinned products, query synonym expansions, and custom boosting rules.
- 💾 **Low Footprint**: Runs on single-node VPS environments with as little as 1 GB RAM.
- 🛡️ **Disaster Recovery**: Automated, single-command backup and restore scripts for PostgreSQL and Typesense.

---

## Supported Operational Modes

Control system resource consumption using the `MERCURY_MODE` environment variable in `.env`:

| Mode | Target Memory | Search Capabilities | AI Chat | Requirements |
| :--- | :--- | :--- | :--- | :--- |
| `lite` | **~300 MB** | BM25 Keyword & Typo Tolerance | Disabled | None |
| `standard` | **~600 MB** | Hybrid (Vector + Keyword) | Disabled | Local Embedder |
| `full` | **~1 GB+** | Hybrid Search + AI Reranking & Chat | Enabled | `GOOGLE_API_KEY` |

---

## Quick Start

### 1. Clone & Configure
```bash
git clone https://github.com/your-org/mercury.git
cd mercury
cp .env.example .env
```

### 2. Start Services
```bash
docker compose up -d
```

### 3. Verify System Health
```bash
bash scripts/smoke_test.sh
```

---

## Production Deployment & Merchant Onboarding

For production setups (`docker-compose.prod.yml`), Mercury initializes with clean databases without demo seed data.

### 1. Onboard a New Merchant Organization
```bash
curl -X POST http://localhost:8000/api/v1/admin/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Storefront",
    "slug": "my-storefront",
    "owner_email": "admin@mystorefront.com"
  }'
```
*(Save the returned `admin_key` for organization management and `search_key` for client-side search).*

### 2. Import Product Catalog
Upload your catalog CSV or JSON feed via the Admin API:
```bash
curl -X POST http://localhost:8000/api/v1/admin/catalog/upload \
  -H "Authorization: Bearer <sk_admin_key>" \
  -F "file=@products.csv"
```

---

## Storefront Search Widget Integration

Embed the Mercury search bar and conversational assistant into your storefront with a single script tag:

```html
<script src="http://your-mercury-host.com/widget/mercury-widget.js" 
        data-api-key="pk_your_search_key" 
        data-endpoint="http://your-mercury-host.com">
</script>
```

---

## Disaster Recovery: Backup & Restore

Mercury includes production backup and restore tools to safeguard PostgreSQL data and Typesense collections.

### Create a Backup
```bash
./scripts/backup.sh
```
Archives are automatically stored in timestamped folders under `./backups/<timestamp>/`.

### Restore from Backup
```bash
./scripts/restore.sh ./backups/<timestamp>
```

---

## Repository Structure

```
mercury/
├── alembic/                 # Database schema migrations
├── app/                     # Core application logic
│   ├── api/                 # FastAPI routes & endpoints
│   ├── domain/              # Business domain models & services
│   ├── infrastructure/      # Database & search clients
│   └── main.py              # Application entrypoint
├── config/                  # Configuration & schema definitions
├── scripts/                 # Maintenance, backup & test scripts
├── tests/                   # Unit & integration test suites
├── widget/                  # Embeddable JS search widget
├── docker-compose.yml       # Development orchestration
├── docker-compose.prod.yml  # Production deployment specification
└── Dockerfile               # Production container image definition
```

---

## License

Mercury is licensed under the **Business Source License 1.1 (BUSL-1.1)**. You are granted permission to self-host and inspect the source code for your own commercial e-commerce storefronts. On the 4th anniversary of this release, the license automatically transitions to **GNU General Public License v3.0 (GPLv3)**.
