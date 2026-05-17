# Pin major.minor for reproducible CI and local Docker validation.
FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY pyproject.toml README.md ./
COPY policies ./policies
COPY src ./src
COPY tests ./tests
COPY scripts ./scripts

RUN pip install --upgrade pip \
    && pip install -e ".[dev]" \
    && python scripts/check_python_version.py

CMD ["python", "-m", "pytest"]
