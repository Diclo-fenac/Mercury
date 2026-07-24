# syntax=docker/dockerfile:1.7
# FastAPI Production Dockerfile
# ==============================================================================
# STAGE 1: Builder
# ==============================================================================
FROM ghcr.io/astral-sh/uv:0.5-python3.11-bookworm-slim AS builder

# Set environment variables for build optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /build

# Build argument for optional GPU/CUDA acceleration
ARG USE_GPU=false

# Install essential build tools for C-extension packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment at /opt/venv
RUN uv venv /opt/venv

# Copy requirements file first for layer caching
COPY requirements.txt ./

# Install all dependencies into /opt/venv
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$USE_GPU" = "true" ] ; then \
        echo "Installing GPU PyTorch dependencies..." && \
        uv pip install torch sentence-transformers -r requirements.txt ; \
    else \
        echo "Installing CPU-only PyTorch dependencies..." && \
        uv pip install torch --index-url https://download.pytorch.org/whl/cpu && \
        uv pip install -r requirements.txt ; \
    fi

# ==============================================================================
# STAGE 2: Production Runner
# ==============================================================================
FROM python:3.11-slim AS runner

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install runtime-only utilities (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-compiled virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source code
COPY . .

# Security hardening: create non-root app user
RUN adduser --disabled-password --gecos '' --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose default HTTP port
EXPOSE 8000

# Health check definition
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Execute application entrypoint script
ENTRYPOINT ["./entrypoint.sh"]