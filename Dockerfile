# ──────────────────────────────────────────────────────────────────────────────
# EveryCheese — Multi-stage Dockerfile
# Author: Sai Saketh Gooty Kase
#
# Stage 1 (builder) — install Python deps into a virtual environment.
# Stage 2 (runtime) — slim final image; copy only the venv + app code.
# ──────────────────────────────────────────────────────────────────────────────

# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# System deps required by psycopg2, Pillow, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Isolate dependencies from the system Python.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements/base.txt requirements/production.txt ./
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r production.txt


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="Sai Saketh Gooty Kase <saisaketh.gootykase@gmail.com>"
LABEL org.opencontainers.image.title="EveryCheese"
LABEL org.opencontainers.image.description="The Ultimate Artisan Cheese Index"

# Runtime-only system deps (libpq for psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy virtual environment from builder.
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source.
WORKDIR /app
COPY . .

# Collect static files at build time.
ENV DJANGO_SETTINGS_MODULE=config.settings.production
RUN python manage.py collectstatic --noinput || true

# Drop privileges.
USER appuser

EXPOSE 8000

# Gunicorn is the production WSGI server.
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "config.wsgi:application"]
