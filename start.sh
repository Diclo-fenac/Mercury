#!/usr/bin/env bash
# =============================================================================
#  Mercury AI Assistant — One-Command Startup
# =============================================================================
#  Usage:
#    ./start.sh              Full startup (infra + backend + frontend)
#    ./start.sh --setup      First-time setup (deps + infra + migrations + indexing)
#    ./start.sh --backend    Backend only (skip frontend)
#    ./start.sh --infra      Infrastructure only (Docker services)
#    ./start.sh --stop       Stop everything
#    ./start.sh --status     Show service status
#    ./start.sh --reset      Stop + wipe Docker volumes + restart fresh
# =============================================================================
set -euo pipefail

# ── Colours & Symbols ─────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Colour

OK="${GREEN}✓${NC}"
FAIL="${RED}✗${NC}"
WARN="${YELLOW}⚠${NC}"
ARROW="${CYAN}→${NC}"
ROCKET="${MAGENTA}🚀${NC}"
GEAR="⚙"
DB="🗄"
GLOBE="🌐"

# ── Project Root ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

# PID file locations (for managed processes)
PID_DIR="$PROJECT_ROOT/.mercury"
BACKEND_PID="$PID_DIR/backend.pid"
FRONTEND_PID="$PID_DIR/frontend.pid"
LOG_DIR="$PID_DIR/logs"
SETUP_MARKER="$PID_DIR/.setup_done"

mkdir -p "$PID_DIR" "$LOG_DIR"

# ── Helper Functions ──────────────────────────────────────────────────────────
banner() {
    echo ""
    echo -e "${MAGENTA}${BOLD}"
    echo "  ╔══════════════════════════════════════════════╗"
    echo "  ║         Mercury AI Assistant  v4.0           ║"
    echo "  ║         ─────────────────────────            ║"
    echo "  ║         One-Command Startup Script           ║"
    echo "  ╚══════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_step() {
    echo -e "\n${BLUE}${BOLD}[$1/${TOTAL_STEPS}]${NC} ${BOLD}$2${NC}"
    echo -e "${DIM}$(printf '%.0s─' {1..50})${NC}"
}

log_ok()   { echo -e "  ${OK}  $1"; }
log_fail() { echo -e "  ${FAIL}  $1"; }
log_warn() { echo -e "  ${WARN}  $1"; }
log_info() { echo -e "  ${ARROW}  $1"; }

check_command() {
    if command -v "$1" &>/dev/null; then
        log_ok "$1 $(command -v "$1" | xargs) $($1 --version 2>/dev/null | head -1 || true)"
        return 0
    else
        log_fail "$1 is not installed"
        return 1
    fi
}

wait_for_port() {
    local host="$1" port="$2" name="$3" timeout="${4:-30}"
    local elapsed=0
    while ! (echo >/dev/tcp/"$host"/"$port") 2>/dev/null; do
        if [ $elapsed -ge $timeout ]; then
            log_fail "$name did not start within ${timeout}s on port $port"
            return 1
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    log_ok "$name is ready on port $port ${DIM}(${elapsed}s)${NC}"
}

kill_pid_file() {
    local pidfile="$1" name="$2"
    if [ -f "$pidfile" ]; then
        local pid
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            for i in {1..5}; do
                kill -0 "$pid" 2>/dev/null || break
                sleep 1
            done
            kill -9 "$pid" 2>/dev/null || true
            log_ok "Stopped $name (PID $pid)"
        else
            log_info "$name was not running"
        fi
        rm -f "$pidfile"
    else
        log_info "$name is not running (no PID file)"
    fi
}

ensure_venv() {
    # Create or activate venv
    VENV_DIR="$PROJECT_ROOT/.venv"
    if [ ! -d "$VENV_DIR" ]; then
        log_info "Creating virtual environment..."
        if [ $HAS_UV -eq 1 ]; then
            uv venv "$VENV_DIR"
        else
            python3 -m venv "$VENV_DIR"
        fi
        log_ok "Virtual environment created at .venv/"
    else
        log_ok "Virtual environment already exists"
    fi

    # Activate it for this script
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    log_ok "Virtual environment activated"
}

install_python_deps() {
    log_info "Installing packages (this may take a minute on first run)..."
    if [ $HAS_UV -eq 1 ]; then
        uv pip install -r requirements.txt --quiet 2>&1 | tail -3
    else
        pip install -r requirements.txt --quiet 2>&1 | tail -3
    fi
    log_ok "Python dependencies installed"
}

start_docker_infra() {
    # Check if Docker daemon is running
    if ! docker info &>/dev/null; then
        log_fail "Docker daemon is not running. Start Docker and re-run."
        exit 1
    fi
    log_ok "Docker daemon is running"

    # Start services
    log_info "Pulling and starting containers..."
    docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null
    log_ok "Docker Compose started"

    # Wait for services to be healthy
    log_info "Waiting for services to become ready..."
    wait_for_port localhost 5432 "PostgreSQL"  30
    wait_for_port localhost 6379 "Redis"       15

    wait_for_port localhost 8108 "Typesense"   30
}

run_migrations() {
    # Check asyncpg
    if ! python3 -c "import asyncpg" 2>/dev/null; then
        log_warn "asyncpg not importable — installing..."
        if [ $HAS_UV -eq 1 ]; then
            uv pip install asyncpg --quiet
        else
            pip install asyncpg --quiet
        fi
    fi

    if [ -f "$PROJECT_ROOT/alembic.ini" ]; then
        log_info "Running alembic upgrade head..."
        if alembic upgrade head 2>"$LOG_DIR/alembic.log"; then
            log_ok "Database migrations applied"
        else
            log_warn "Migrations failed (see $LOG_DIR/alembic.log) — may already be up to date"
            tail -3 "$LOG_DIR/alembic.log" 2>/dev/null | while IFS= read -r line; do
                echo -e "       ${DIM}$line${NC}"
            done
        fi
    else
        log_warn "No alembic.ini found — skipping migrations"
    fi
}

# ── STOP ──────────────────────────────────────────────────────────────────────
do_stop() {
    echo -e "\n${BOLD}Stopping Mercury services...${NC}\n"

    kill_pid_file "$FRONTEND_PID" "Frontend"
    kill_pid_file "$BACKEND_PID" "Backend"

    echo ""
    read -r -p "Also stop Docker infrastructure? (y/N): " reply
    if [[ "$reply" =~ ^[Yy]$ ]]; then
        docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true
        log_ok "Docker services stopped"
    fi
    echo -e "\n${OK}  All stopped.\n"
    exit 0
}

# ── STATUS ────────────────────────────────────────────────────────────────────
do_status() {
    echo -e "\n${BOLD}Mercury Service Status${NC}\n"

    # Setup status
    echo -e "${CYAN}Setup:${NC}"
    if [ -f "$SETUP_MARKER" ]; then
        echo -e "  ${OK}  First-time setup completed on $(cat "$SETUP_MARKER")"
    else
        echo -e "  ${WARN}  First-time setup has ${YELLOW}not been run${NC}"
        echo -e "       Run ${BOLD}./start.sh --setup${NC} to initialize"
    fi

    # Docker services
    echo -e "\n${CYAN}Docker Infrastructure:${NC}"
    local services=("postgres:5432" "redis:6379" "typesense:8108")
    for svc in "${services[@]}"; do
        local name="${svc%%:*}"
        local port="${svc##*:}"
        if (echo >/dev/tcp/localhost/"$port") 2>/dev/null; then
            echo -e "  ${OK}  ${name} — ${GREEN}running${NC} on port ${port}"
        else
            echo -e "  ${FAIL}  ${name} — ${RED}not running${NC} (port ${port})"
        fi
    done

    # Backend
    echo -e "\n${CYAN}Application:${NC}"
    if [ -f "$BACKEND_PID" ] && kill -0 "$(cat "$BACKEND_PID")" 2>/dev/null; then
        echo -e "  ${OK}  Backend — ${GREEN}running${NC} (PID $(cat "$BACKEND_PID"))"
    elif (echo >/dev/tcp/localhost/8000) 2>/dev/null; then
        echo -e "  ${OK}  Backend — ${GREEN}running${NC} (external process)"
    else
        echo -e "  ${FAIL}  Backend — ${RED}not running${NC}"
    fi

    # Frontend
    if [ -f "$FRONTEND_PID" ] && kill -0 "$(cat "$FRONTEND_PID")" 2>/dev/null; then
        echo -e "  ${OK}  Frontend — ${GREEN}running${NC} (PID $(cat "$FRONTEND_PID"))"
    elif (echo >/dev/tcp/localhost/5173) 2>/dev/null; then
        echo -e "  ${OK}  Frontend — ${GREEN}running${NC} (external process)"
    else
        echo -e "  ${FAIL}  Frontend — ${RED}not running${NC}"
    fi

    echo ""
    exit 0
}

# ── RESET ─────────────────────────────────────────────────────────────────────
do_reset() {
    echo -e "\n${RED}${BOLD}⚠  This will destroy all Docker volumes (databases, indexes, vectors).${NC}"
    read -r -p "Are you sure? (y/N): " reply
    if [[ ! "$reply" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi

    kill_pid_file "$FRONTEND_PID" "Frontend"
    kill_pid_file "$BACKEND_PID" "Backend"
    docker compose down -v 2>/dev/null || docker-compose down -v 2>/dev/null || true
    rm -f "$SETUP_MARKER"
    log_ok "All services stopped, volumes removed, setup marker cleared"

    echo -e "\n${ARROW}  Restarting with fresh setup...\n"
    exec "$0" --setup
}

# ══════════════════════════════════════════════════════════════════════════════
#  FIRST-TIME SETUP
# ══════════════════════════════════════════════════════════════════════════════
do_setup() {
    TOTAL_STEPS=8
    banner
    echo -e "  ${CYAN}${BOLD}Running first-time setup...${NC}"
    echo -e "  ${DIM}This installs dependencies, starts infrastructure, creates${NC}"
    echo -e "  ${DIM}databases, runs migrations, and indexes search data.${NC}"

    # ── Step 1: Prerequisites ─────────────────────────────────────────────
    log_step 1 "${GEAR}  Checking Prerequisites"

    MISSING=0
    check_command python3 || MISSING=1
    check_command docker  || MISSING=1

    HAS_UV=0
    if command -v uv &>/dev/null; then
        log_ok "uv (fast Python package manager) detected"
        HAS_UV=1
    elif command -v pip &>/dev/null; then
        log_ok "pip detected (fallback)"
    else
        log_fail "No Python package manager found (need uv or pip)"
        MISSING=1
    fi

    check_command node || MISSING=1
    check_command npm  || MISSING=1

    if [ $MISSING -eq 1 ]; then
        echo ""
        log_fail "Missing prerequisites. Install them and re-run."
        echo ""
        echo -e "  ${BOLD}Required:${NC}"
        echo -e "    • Python 3.10+    ${DIM}→ https://python.org${NC}"
        echo -e "    • Docker + Compose ${DIM}→ https://docs.docker.com/get-docker${NC}"
        echo -e "    • Node.js 18+     ${DIM}→ https://nodejs.org${NC}"
        echo -e "    • uv (recommended) ${DIM}→ curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
        echo ""
        exit 1
    fi

    # ── Step 2: Environment Configuration ─────────────────────────────────
    log_step 2 "${GEAR}  Environment Configuration"

    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_warn ".env file not found"
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            log_ok "Created .env from .env.example"
        else
            log_fail "No .env.example found. Cannot continue."
            exit 1
        fi
    else
        log_ok ".env file exists"
    fi

    # Validate critical keys
    source <(grep -E '^(SECRET_KEY|GOOGLE_API_KEY|DEBUG|DATABASE_URL)=' "$PROJECT_ROOT/.env" 2>/dev/null || true)

    ENV_ISSUES=0
    if [ -z "${SECRET_KEY:-}" ] || [ "$SECRET_KEY" = "your-super-secret-key-here" ]; then
        log_warn "SECRET_KEY is unset or a placeholder"
        echo -e "       ${DIM}Generate one with: openssl rand -hex 32${NC}"
        echo -e "       ${DIM}Using dev default for now...${NC}"
        ENV_ISSUES=1
    else
        log_ok "SECRET_KEY is configured"
    fi

    if [ -z "${GOOGLE_API_KEY:-}" ] || [ "$GOOGLE_API_KEY" = "your-google-api-key" ]; then
        log_warn "GOOGLE_API_KEY is unset — AI/embedding features will NOT work"
        echo -e "       ${DIM}Get one from: https://aistudio.google.com/apikey${NC}"
        ENV_ISSUES=1
    else
        log_ok "GOOGLE_API_KEY is configured"
    fi


    if [ $ENV_ISSUES -gt 0 ]; then
        echo ""
        echo -e "  ${YELLOW}${BOLD}Some environment keys are missing.${NC}"
        read -r -p "  Continue anyway? (Y/n): " reply
        if [[ "$reply" =~ ^[Nn]$ ]]; then
            echo -e "\n  Edit ${BOLD}.env${NC} and re-run ${BOLD}./start.sh --setup${NC}\n"
            exit 0
        fi
    fi

    # ── Step 3: Docker Infrastructure ─────────────────────────────────────
    log_step 3 "${DB}  Starting Docker Infrastructure"
    start_docker_infra

    # ── Step 4: Python Dependencies ───────────────────────────────────────
    log_step 4 "${GEAR}  Installing Python Dependencies"
    ensure_venv
    install_python_deps

    # Verify critical imports
    log_info "Verifying critical packages..."
    local verify_pkgs=("fastapi" "uvicorn" "sqlalchemy" "asyncpg" "redis" "pydantic")
    local verify_ok=true
    for pkg in "${verify_pkgs[@]}"; do
        if python3 -c "import $pkg" 2>/dev/null; then
            log_ok "$pkg"
        else
            log_fail "$pkg — import failed"
            verify_ok=false
        fi
    done
    if [ "$verify_ok" = false ]; then
        log_warn "Some packages failed to import. The app may not start correctly."
    fi

    # ── Step 5: Database Migrations ───────────────────────────────────────
    log_step 5 "${DB}  Database Migrations"
    run_migrations

    # ── Step 6: Search Engine Setup ───────────────────────────────────────
    log_step 6 "${DB}  Search Engine Setup"

    # Typesense collection
    log_info "Setting up Typesense collection..."
    if python3 -c "
import asyncio, sys, json
sys.path.insert(0, '.')
from app.infrastructure.search.typesense import TypesenseClient
from app.settings import get_settings
schema = {
    'name': 'products',
    'fields': [
        {'name': 'id', 'type': 'string'},
        {'name': 'title', 'type': 'string'},
        {'name': 'brand', 'type': 'string', 'facet': True},
        {'name': 'category', 'type': 'string', 'facet': True},
        {'name': 'sub_category', 'type': 'string', 'optional': True, 'facet': True},
        {'name': 'description', 'type': 'string', 'optional': True},
        {'name': 'rating', 'type': 'float'},
        {'name': 'stock', 'type': 'string', 'optional': True},
        {'name': 'selling_price', 'type': 'float', 'optional': True}
    ],
    'default_sorting_field': 'rating'
}
async def setup():
    s = get_settings()
    c = TypesenseClient(host=s.TYPESENSE_HOST, port=s.TYPESENSE_PORT, api_key=s.TYPESENSE_API_KEY)
    await c.connect()
    if not await c.collection_exists('products'):
        await c.create_collection(schema)
        print('CREATED')
    else:
        print('EXISTS')
    await c.close()
asyncio.run(setup())
" 2>"$LOG_DIR/typesense_setup.log"; then
        log_ok "Typesense 'products' collection ready"
    else
        log_warn "Could not set up Typesense collection (see $LOG_DIR/typesense_setup.log)"
    fi

    # ── Step 7: Data Indexing ─────────────────────────────────────────────
    log_step 7 "${DB}  Data Indexing"

    PRODUCTS_FILE="$PROJECT_ROOT/products.jsonl"
    if [ -f "$PRODUCTS_FILE" ]; then
        PRODUCT_COUNT=$(wc -l < "$PRODUCTS_FILE")
        log_ok "Found products.jsonl (${PRODUCT_COUNT} products)"

        # Index into Typesense
        log_info "Indexing products into Typesense..."
        if python3 scripts/index_typesense.py > "$LOG_DIR/typesense_index.log" 2>&1; then
            log_ok "Typesense indexing complete"
        else
            log_warn "Typesense indexing failed (see $LOG_DIR/typesense_index.log)"
            tail -3 "$LOG_DIR/typesense_index.log" 2>/dev/null | while IFS= read -r line; do
                echo -e "       ${DIM}$line${NC}"
            done
        fi


    else
        log_warn "No products.jsonl found — skipping data indexing"
        echo -e "       ${DIM}The app will start but search will return empty results.${NC}"
        echo -e "       ${DIM}Place a products.jsonl in the project root and re-run --setup.${NC}"
    fi

    # ── Step 8: Frontend Dependencies ─────────────────────────────────────
    log_step 8 "${GEAR}  Frontend Dependencies"

    FRONTEND_DIR="$PROJECT_ROOT/app/frontend"
    if [ -d "$FRONTEND_DIR" ] && [ -f "$FRONTEND_DIR/package.json" ]; then
        log_info "Running npm install..."
        (cd "$FRONTEND_DIR" && npm install --silent 2>&1 | tail -3)
        log_ok "Frontend packages installed"
    else
        log_warn "No frontend found at app/frontend/"
    fi

    # ── Mark setup as done ────────────────────────────────────────────────
    date '+%Y-%m-%d %H:%M:%S' > "$SETUP_MARKER"

    # ── Summary ───────────────────────────────────────────────────────────
    echo ""
    echo -e "${GREEN}${BOLD}"
    echo "  ╔══════════════════════════════════════════════╗"
    echo "  ║       First-time setup complete! ✅          ║"
    echo "  ╚══════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "  ${BOLD}What was set up:${NC}"
    echo -e "    ${OK}  Docker services (Postgres, Redis, Typesense)"
    echo -e "    ${OK}  Python virtual environment and dependencies"
    echo -e "    ${OK}  Database schema (Alembic migrations)"
    echo -e "    ${OK}  Search engine collections"
    [ -f "$PRODUCTS_FILE" ] && echo -e "    ${OK}  Product data indexed"
    echo -e "    ${OK}  Frontend dependencies"
    echo ""
    echo -e "  ${BOLD}Next: Start the app with:${NC}"
    echo -e "    ${CYAN}./start.sh${NC}"
    echo ""

    exit 0
}

# ── Parse Arguments ───────────────────────────────────────────────────────────
MODE="full"  # full | backend | infra | setup
for arg in "$@"; do
    case "$arg" in
        --setup)    do_setup       ;;
        --backend)  MODE="backend" ;;
        --infra)    MODE="infra"   ;;
        --stop)     do_stop        ;;
        --status)   do_status      ;;
        --reset)    do_reset       ;;
        --help|-h)
            echo ""
            echo -e "${BOLD}Mercury AI Assistant — Startup Script${NC}"
            echo ""
            echo -e "  ${BOLD}Usage:${NC} ./start.sh [OPTIONS]"
            echo ""
            echo -e "  ${BOLD}Options:${NC}"
            echo -e "    ${CYAN}(no args)${NC}    Full startup (infra + backend + frontend)"
            echo -e "    ${CYAN}--setup${NC}      First-time setup (install everything from scratch)"
            echo -e "    ${CYAN}--backend${NC}    Start backend only (skip frontend)"
            echo -e "    ${CYAN}--infra${NC}      Start Docker services only"
            echo -e "    ${CYAN}--stop${NC}       Stop all running services"
            echo -e "    ${CYAN}--status${NC}     Show service status"
            echo -e "    ${CYAN}--reset${NC}      Stop + wipe volumes + re-setup from scratch"
            echo -e "    ${CYAN}--help${NC}       Show this help"
            echo ""
            echo -e "  ${BOLD}First time?${NC} Run ${CYAN}./start.sh --setup${NC}"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${FAIL} Unknown option: $arg"
            echo "Run ./start.sh --help for usage."
            exit 1
            ;;
    esac
done

# ══════════════════════════════════════════════════════════════════════════════
#  AUTO-DETECT FIRST RUN
# ══════════════════════════════════════════════════════════════════════════════
if [ ! -f "$SETUP_MARKER" ]; then
    echo ""
    echo -e "  ${WARN}  ${YELLOW}${BOLD}First-time run detected!${NC}"
    echo -e "  ${DIM}  Setup has not been completed yet.${NC}"
    echo ""
    read -r -p "  Run first-time setup now? (Y/n): " reply
    if [[ ! "$reply" =~ ^[Nn]$ ]]; then
        do_setup
    else
        echo -e "\n  ${DIM}Skipping setup. Run ${BOLD}./start.sh --setup${NC}${DIM} when ready.${NC}\n"
    fi
fi

# ══════════════════════════════════════════════════════════════════════════════
#  NORMAL STARTUP (after setup is done)
# ══════════════════════════════════════════════════════════════════════════════
case "$MODE" in
    full)    TOTAL_STEPS=5 ;;
    backend) TOTAL_STEPS=4 ;;
    infra)   TOTAL_STEPS=2 ;;
esac

banner

# ── Step 1: Quick Prerequisite Check ──────────────────────────────────────────
log_step 1 "${GEAR}  Checking Prerequisites"

MISSING=0
HAS_UV=0
command -v python3 &>/dev/null || MISSING=1
command -v docker &>/dev/null  || MISSING=1
command -v uv &>/dev/null && HAS_UV=1

if [ $MISSING -eq 1 ]; then
    log_fail "Missing python3 or docker. Run ${BOLD}./start.sh --setup${NC} for details."
    exit 1
fi
log_ok "Prerequisites OK"

# .env check
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    log_fail ".env not found. Run ${BOLD}./start.sh --setup${NC}"
    exit 1
fi
log_ok ".env file exists"

# ── Step 2: Docker Infrastructure ─────────────────────────────────────────────
log_step 2 "${DB}  Starting Docker Infrastructure"
start_docker_infra

if [ "$MODE" = "infra" ]; then
    echo -e "\n${ROCKET}  ${GREEN}${BOLD}Infrastructure is ready!${NC}\n"
    echo -e "  PostgreSQL  ${DIM}→${NC}  localhost:5432"
    echo -e "  Redis       ${DIM}→${NC}  localhost:6379"

    echo -e "  Typesense   ${DIM}→${NC}  localhost:8108"
    echo ""
    exit 0
fi

# ── Step 3: Activate Venv & Run Migrations ────────────────────────────────────
log_step 3 "${DB}  Preparing Backend"

ensure_venv

# Quick migration check (fast — only runs pending)
log_info "Checking database migrations..."
run_migrations

# ── Step 4: Start Backend ─────────────────────────────────────────────────────
log_step 4 "${GLOBE}  Starting Backend Server"

# Kill old backend if running
if [ -f "$BACKEND_PID" ] && kill -0 "$(cat "$BACKEND_PID")" 2>/dev/null; then
    log_info "Stopping existing backend (PID $(cat "$BACKEND_PID"))..."
    kill "$(cat "$BACKEND_PID")" 2>/dev/null || true
    sleep 2
fi

# Start uvicorn in background
log_info "Launching FastAPI on port 8000..."
VENV_DIR="$PROJECT_ROOT/.venv"
nohup "$VENV_DIR/bin/python" -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    > "$LOG_DIR/backend.log" 2>&1 &
echo $! > "$BACKEND_PID"
log_ok "Backend started (PID $(cat "$BACKEND_PID"))"
log_info "Logs: ${DIM}$LOG_DIR/backend.log${NC}"

# Wait for it
wait_for_port localhost 8000 "FastAPI Backend" 20

# Quick health check
if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    log_ok "Health check passed ${GREEN}✓${NC}"
else
    log_warn "Health endpoint not responding yet (may still be initializing)"
fi

if [ "$MODE" = "backend" ]; then
    echo -e "\n${ROCKET}  ${GREEN}${BOLD}Backend is running!${NC}\n"
    echo -e "  API       ${DIM}→${NC}  http://localhost:8000"
    echo -e "  Docs      ${DIM}→${NC}  http://localhost:8000/docs"
    echo -e "  Health    ${DIM}→${NC}  http://localhost:8000/health"
    echo -e "  Logs      ${DIM}→${NC}  $LOG_DIR/backend.log"
    echo -e "\n  Stop with: ${BOLD}./start.sh --stop${NC}\n"
    exit 0
fi

# ── Step 5: Start Frontend ────────────────────────────────────────────────────
log_step 5 "${GLOBE}  Starting Frontend Dev Server"

FRONTEND_DIR="$PROJECT_ROOT/app/frontend"
if [ -d "$FRONTEND_DIR" ] && [ -f "$FRONTEND_DIR/package.json" ]; then
    # Kill old frontend if running
    if [ -f "$FRONTEND_PID" ] && kill -0 "$(cat "$FRONTEND_PID")" 2>/dev/null; then
        log_info "Stopping existing frontend (PID $(cat "$FRONTEND_PID"))..."
        kill "$(cat "$FRONTEND_PID")" 2>/dev/null || true
        sleep 2
    fi

    # Ensure node_modules
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        log_info "Running npm install..."
        (cd "$FRONTEND_DIR" && npm install --silent 2>&1 | tail -3)
    fi

    log_info "Launching Vite dev server..."
    (cd "$FRONTEND_DIR" && nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
     echo $! > "$FRONTEND_PID")
    log_ok "Frontend started (PID $(cat "$FRONTEND_PID"))"
    log_info "Logs: ${DIM}$LOG_DIR/frontend.log${NC}"

    wait_for_port localhost 5173 "Vite Frontend" 15 || true
else
    log_warn "Skipping frontend (not found at app/frontend/)"
fi

# ══════════════════════════════════════════════════════════════════════════════
#  Done!
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${MAGENTA}${BOLD}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║           Mercury is running! 🚀             ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "  ${CYAN}Backend${NC}"
echo -e "    API        ${DIM}→${NC}  ${GREEN}http://localhost:8000${NC}"
echo -e "    Swagger    ${DIM}→${NC}  ${GREEN}http://localhost:8000/docs${NC}"
echo -e "    Health     ${DIM}→${NC}  ${GREEN}http://localhost:8000/health${NC}"
echo -e "    WebSocket  ${DIM}→${NC}  ${GREEN}ws://localhost:8000/ws${NC}"
echo ""
echo -e "  ${CYAN}Frontend${NC}"
echo -e "    React App  ${DIM}→${NC}  ${GREEN}http://localhost:5173${NC}"
echo ""
echo -e "  ${CYAN}Infrastructure${NC}"
echo -e "    PostgreSQL ${DIM}→${NC}  localhost:5432"
echo -e "    Redis      ${DIM}→${NC}  localhost:6379"

echo -e "    Typesense  ${DIM}→${NC}  localhost:8108"
echo ""
echo -e "  ${CYAN}Logs${NC}"
echo -e "    Backend    ${DIM}→${NC}  tail -f $LOG_DIR/backend.log"
echo -e "    Frontend   ${DIM}→${NC}  tail -f $LOG_DIR/frontend.log"
echo ""
echo -e "  ${CYAN}Commands${NC}"
echo -e "    Stop all   ${DIM}→${NC}  ${BOLD}./start.sh --stop${NC}"
echo -e "    Status     ${DIM}→${NC}  ${BOLD}./start.sh --status${NC}"
echo -e "    Reset all  ${DIM}→${NC}  ${BOLD}./start.sh --reset${NC}"
echo ""
