# FastAPI Production Dockerfile
# ==============================================================================
# STAGE 1: Builder
# ==============================================================================
FROM python:3.11-slim AS builder

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build-time dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual environment to isolate installed dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Add a build argument for GPU support
ARG USE_GPU=false

# Copy requirements first for better caching
COPY requirements.txt .

# PyTorch is ~2.5GB with CUDA (default), but only ~150MB with CPU-only.
# We strip torch and sentence-transformers from requirements.txt to install them separately based on the flag
RUN if [ "$USE_GPU" = "true" ] ; then \
        echo "Installing GPU PyTorch dependencies..." && \
        pip install --no-cache-dir torch>=2.0.0 sentence-transformers>=2.2.0 ; \
    else \
        echo "Installing CPU-only PyTorch dependencies to save ~2.3GB..." && \
        pip install --no-cache-dir torch>=2.0.0 --index-url https://download.pytorch.org/whl/cpu && \
        pip install --no-cache-dir sentence-transformers>=2.2.0 ; \
    fi

# Now install the rest of the requirements
RUN grep -v -E '^(torch|sentence-transformers)' requirements.txt > req_filtered.txt && \
    pip install --no-cache-dir -r req_filtered.txt && \
    rm req_filtered.txt

# ==============================================================================
# STAGE 2: Runtime Runner
# ==============================================================================
FROM python:3.11-slim AS runner

# Set environment variables for execution
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install runtime-only dependencies (e.g. curl for health check)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY . .

# Create non-root user for security hardiness
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application via entrypoint script
ENTRYPOINT ["./entrypoint.sh"]