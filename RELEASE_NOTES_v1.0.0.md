# Release Notes — Mercury Search v1.0.0 (Self-Hosted GA)

We are thrilled to announce the General Availability (GA) release of **Mercury Search v1.0.0**, a self-hosted, multi-tenant AI-powered e-commerce search and recommendation service designed for speed, isolation, and plug-and-play simplicity.

---

## 🚀 Supported Setup (One-Command Deploy)

Mercury is built from the ground up for seamless self-hosting via Docker Compose. No external SaaS subscriptions or managed cloud databases are required.

```bash
# Clone and configure
git clone https://github.com/your-org/mercury.git
cd mercury
cp .env.example .env

# Boot the entire stack (FastAPI + PostgreSQL + Redis + Typesense)
docker compose up --build -d
```
Within seconds, the backend auto-provisions databases, executes Alembic schemas, seeds demo e-commerce data, and serves the React Admin Dashboard directly from port `8000`.

---

## 💻 Minimum Machine Requirements

Mercury's architectural footprint is aggressively optimized for single-node deployments:
- **CPU**: 1 vCPU (2+ vCPUs recommended for concurrent indexing)
- **RAM**: 1 GB Minimum (Idles at ~380 MB total RAM across all containers; 2 GB recommended for production catalogs >50k products)
- **Disk**: 10 GB SSD storage (for Postgres WAL and Typesense memory-mapped index files)
- **OS**: Linux (Debian/Ubuntu/Alpine) or macOS with Docker Engine 24+ and Docker Compose v2+

---

## 📥 Supported Ingestion Sources

Mercury's ETL ingestion pipeline supports multiple flexible ingestion patterns:
1. **CSV / TAB Uploads**: Direct drag-and-drop file upload via the Admin Dashboard Ingestion Wizard with visual schema field mapping.
2. **JSON Feeds**: Support for nested e-commerce product feeds (Shopify, WooCommerce, Magento exports).
3. **Webhook API**: Real-time programmatic indexing via HTTP POST endpoints (`/api/v1/ingest/webhook`) with secret token verification and HMAC signature support.
4. **Manual Catalog CRUD**: Direct REST API management for individual product creation and updates.

---

## ⚠️ Known Limitations (v1.0.0)

- **Single-Node Scaling**: v1.0.0 is optimized for single-machine vertical scaling. Distributed horizontal clustering (e.g., multi-node Typesense Raft clusters and PostgreSQL read-replicas) is planned for v2.0.
- **LLM Provider Dependency**: While lexical and vector search are 100% self-hosted and offline-capable, the Conversational AI Assistant requires an external API key (Google Gemini / OpenAI / Anthropic) configured in `.env`.
- **Rate Limiting Granularity**: API rate limits are currently enforced per origin/API key in Redis. IP-based fallback rate limiting requires a reverse proxy (e.g., Nginx, Traefik, or Cloudflare) in front of the Docker container.

---

## 🔒 Software License Notice

Mercury Search v1.0.0 is licensed under the **Business Source License 1.1 (BUSL-1.1)**.
- **What you CAN do**: Inspect the source code, modify it, audit it for security, and self-host it for any internal or commercial e-commerce storefronts you own or operate.
- **What you CANNOT do**: Offer Mercury Search itself as a commercial hosted/managed SaaS offering or search-as-a-service to third parties.
- **Open-Source Conversion**: On the 4th anniversary of this release date, this version will automatically convert to the OSI-approved **GNU General Public License v3.0 (GPLv3)**.
