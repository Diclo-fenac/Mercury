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

## Demo Dataset & Onboarding

When you run `docker compose up`, Mercury automatically seeds a demo electronics catalog containing laptops, smartphones, and accessories.

You can verify it works by onboarding a test tenant:
```bash
curl -X POST http://localhost:8000/api/v1/admin/onboard \
  -H "Content-Type: application/json" \
  -d '{"name": "Demo Store", "slug": "demo", "owner_email": "demo@store.com"}'
```
This returns a public `search_key` and a private `admin_key` for your store.

---

## Troubleshooting Common Failures

| Issue | Cause | Fix |
|-------|-------|-----|
| **App container crashes immediately** | Missing `GOOGLE_API_KEY` in `full` mode. | Edit `.env` to set `MERCURY_MODE="standard"` or provide an API key. |
| **Search returns 0 results** | Typesense indexing failed or wasn't seeded. | Run `docker compose exec app python scripts/index_typesense.py` manually. |
| **High Latency (> 1s)** | VPS is swapping memory to disk. | Ensure you have at least 1GB of RAM, or downgrade to `MERCURY_MODE="lite"`. |
| **Docker Permission Denied** | User is not in the `docker` group. | Run commands with `sudo` or add your user to the docker group: `sudo usermod -aG docker $USER`. |

*For Disaster Recovery, Backup, and SRE Guidelines, please see [docs/RUNBOOK.md](docs/RUNBOOK.md).*
