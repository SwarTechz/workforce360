# ================================
# 1. BASE IMAGE (BUILDER STAGE)
# ================================
FROM python:3.12-slim AS builder

# Install system dependencies (needed for psycopg, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy pyproject + lock file
COPY pyproject.toml uv.lock ./

# Create venv
RUN python -m venv /opt/venv

# Export requirements from uv.lock
RUN uv export --format requirements.txt --output-file requirements.txt

# Install dependencies into venv
RUN uv pip install --python /opt/venv/bin/python -r requirements.txt


# Copy application code (not installed)
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini


# ================================
# 2. RUNTIME IMAGE (PRODUCTION STAGE)
# ================================
FROM python:3.12-slim

# Create non-root user
RUN useradd -m pavi

# Install minimal runtime system dependencies
# Install system dependencies + PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use the venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy app + alembic artifacts
COPY --from=builder /app/app ./app
COPY --from=builder /app/alembic ./alembic
COPY --from=builder /app/alembic.ini ./alembic.ini

# Expose FastAPI port
EXPOSE 8000

# Switch to non-root user
USER pavi

# Run API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
