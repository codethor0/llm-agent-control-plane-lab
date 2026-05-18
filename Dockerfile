# Pin major.minor for reproducible CI and local Docker validation.
FROM python:3.12-slim-bookworm

# Apply Debian security updates in the image (supply-chain; no app logic change).
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ACP_ENVIRONMENT=local

COPY pyproject.toml README.md ./
COPY policies ./policies
COPY src ./src
COPY tests ./tests
COPY scripts ./scripts

RUN pip install --upgrade pip \
    && pip install -e ".[dev]" \
    && python scripts/check_python_version.py \
    && mkdir -p /app/var/audit \
    && groupadd -r appuser \
    && useradd -r -g appuser -d /app appuser \
    && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "from agent_control_plane.config import load_config_from_env; load_config_from_env().validate()"

CMD ["python", "-m", "pytest"]
