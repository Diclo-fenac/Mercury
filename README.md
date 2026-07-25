# Mercury AI Assistant

Mercury is a multi-tenant AI-powered search and recommendation system built with FastAPI, Typesense, PostgreSQL, Redis, and Google Gemini.

Designed to be truly plug-and-play for small e-commerce businesses, it features a highly optimized footprint for single-node deployments.

---

## Quick Start (Install Steps)

Mercury can be deployed with a single command. Out of the box, it automatically provisions databases, runs migrations, and seeds demo data for you to test immediately.

```bash
# 1. Clone the repository
git clone https://github.com/your-org/mercury.git
cd mercury

# 2. Setup your environment
cp .env.example .env

# 3. Start the system (One-command Deploy)
docker compose up -d

# 4. Verify deployment
bash scripts/smoke_test.sh
```

To rollback or stop:
```bash
# One-command Rollback / Stop
docker compose down
```

---

## Hardware Requirements

Mercury is highly optimized and heavily modular.

**Minimum Specs:**
- **1 GB RAM VPS** (e.g. DigitalOcean Basic Droplet)
- **1 vCPU**
- **10 GB Disk Space**

*Note on 1GB RAM Guarantee:* Mercury comfortably boots under 512MB RAM in `lite` mode.
- **Idle RAM:** ~380MB (across all containers)
- **Startup Time:** ~12 seconds
- **First-Query Latency:** < 50ms

---

## Supported Modes

Mercury uses the `MERCURY_MODE` environment variable in your `.env` to gate heavy ML resources dynamically:

| Mode       | Memory Target | Search Tech                    | Chat Fallback | Requirements |
|------------|---------------|--------------------------------|---------------|--------------|
| `lite`     | ~300MB        | BM25 + Typo (Typesense only)   | Disabled      | None         |
| `standard` | ~600MB        | Vector + Hybrid (Local Embed)  | Disabled      | None         |
| `full`     | ~1GB+         | Hybrid + AI Rerank & Chat      | Enabled       | `GOOGLE_API_KEY` |

---

## Demo Dataset & First-Run Bootstrap

Mercury supports two distinct deployment profiles:

### 1. Development Mode (`docker compose up -d`)
When started via `docker-compose.yml`, Mercury automatically runs an initialization seeder that provisions the database, applies Alembic migrations, and seeds a demo electronics catalog (laptops, phones, accessories) so you can test immediately.

### 2. Production Mode (`docker compose -f docker-compose.prod.yml up -d`)
To maintain a clean database in production, `docker-compose.prod.yml` does **not** auto-seed demo data. After starting production, onboard your merchant organization:
```bash
# 1. Onboard merchant organization
curl -X POST http://localhost:8000/api/v1/admin/onboard \
  -H "Content-Type: application/json" \
  -d '{"name": "My E-Commerce Store", "slug": "my-store", "owner_email": "admin@mystore.com"}'
```
*(Save the returned `admin_key` and `search_key`)*.

If you wish to populate demo data in production for evaluation:
```bash
# Optional: Seed demo catalog into production
docker compose -f docker-compose.prod.yml exec app python scripts/seed_products.py
docker compose -f docker-compose.prod.yml exec app python scripts/index_typesense.py
```

---

## Widget Installation Guide

Once your catalog is indexed, integrate the search widget into your storefront with a single script tag:

```html
<!-- 1. Include the Mercury Search Widget Bundle -->
<script src="http://your-mercury-server.com/widget/mercury-search.min.js" 
        data-api-key="pk_your_public_search_key_here" 
        data-endpoint="http://your-mercury-server.com">
</script>
```

**Widget Features:**
- **Instant Typeahead:** < 30ms latency keyword suggestions.
- **Hybrid Search & Filtering:** Vector similarity + exact keyword matching with facet filters.
- **AI RAG Assistant:** Grounded conversational answers with clickable product citations (`full` mode).

---

## Security Hardening Guide

For self-hosted production deployments:
1. **API Key Separation:** Never expose your private `sk_*` admin key in frontend code or widget configurations. Only distribute restricted `pk_*` public search keys to browsers.
2. **Reverse Proxy & SSL/TLS:** Always place Mercury behind an HTTPS edge proxy (such as Cloudflare, Nginx, or Traefik) to encrypt traffic and provide IP-based DDoS protection.
3. **Secret Key Rotation:** Ensure `SECRET_KEY` in your `.env` is set to a secure, random 32-byte hexadecimal string before exposing ports to the public internet.

---

## Troubleshooting Common Failures

| Issue | Cause | Fix |
|-------|-------|-----|
| **App container crashes immediately** | Missing `GOOGLE_API_KEY` in `full` mode. | Edit `.env` to set `MERCURY_MODE="standard"` or provide an API key. |
| **Search returns 0 results** | Typesense indexing failed or wasn't seeded. | Run `docker compose exec app python scripts/index_typesense.py` manually. |
| **High Latency (> 1s)** | VPS is swapping memory to disk. | Ensure you have at least 1GB of RAM, or downgrade to `MERCURY_MODE="lite"`. |
| **Docker Permission Denied** | User is not in the `docker` group. | Run commands with `sudo` or add your user to the docker group: `sudo usermod -aG docker $USER`. |

---

## Disaster Recovery: Backup & Restore

Mercury includes automated scripts for full disaster recovery, capturing both your PostgreSQL relational database and your Typesense search indexes.

### Create a Backup
To create a timestamped backup archive of PostgreSQL and Typesense:
```bash
./scripts/backup.sh
```
The archive will be saved under `./backups/<timestamp>/`.

### Restore from Backup
To stop services, wipe existing corrupted volumes, and restore cleanly from a backup directory:
```bash
./scripts/restore.sh ./backups/<timestamp>
```

---

## Documentation & Production Proofs

- **Disaster Recovery, Backup & Upgrade Rollback:** See [docs/RUNBOOK.md](docs/RUNBOOK.md) for step-by-step SQL restore commands, Docker volume catalogs, and rollback procedures.
- **Load, Performance & Resource Benchmarks:** See [docs/BENCHMARKS.md](docs/BENCHMARKS.md) for measured latency distributions (P50/P95/P99), catalog scale limits (up to 50k SKUs on 1GB RAM), and service memory footprints.
- **Detailed Widget Architecture:** See [docs/WIDGET.md](docs/WIDGET.md).
- **Frontend & Dashboard Roadmap:** See [docs/IMPLEMENTATION_ROADMAP_P1_P3.md](docs/IMPLEMENTATION_ROADMAP_P1_P3.md).
- **Release Notes:** See [RELEASE_NOTES_v1.0.0.md](RELEASE_NOTES_v1.0.0.md).

---

## Software License

Mercury is licensed under the **Business Source License 1.1 (BUSL-1.1)**. You are permitted to inspect, modify, and self-host Mercury for any internal or commercial e-commerce storefronts you operate. Offering Mercury itself as a commercial hosted/managed search SaaS to third parties is strictly prohibited. On the 4th anniversary of this release, this license automatically converts to Apache 2.0.
