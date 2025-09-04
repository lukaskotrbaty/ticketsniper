# Stage 1: Base - Installs Python and Poetry
FROM python:3.10-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install Poetry
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    apt-get remove -y --purge curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Stage 2: Builder - Installs dependencies
FROM base AS builder

WORKDIR /code

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install production dependencies
RUN poetry install --no-interaction --no-ansi --no-root --only main

# Stage 3: Development Image - Includes dev dependencies and runs with reload
FROM builder AS development

# Install development dependencies on top of production ones
# This leverages the cache from the previous stage
RUN poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY ./app /code/app

# Create a non-root user and set ownership
RUN groupadd -r appgroup && useradd --no-log-init -r -g appgroup appuser
# Create celery state directory and set ownership
RUN mkdir -p /var/run/celery && chown -R appuser:appgroup /code /var/run/celery
USER appuser

EXPOSE 8000

# Run with reload for development using poetry run
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/code/app"]

# Stage 4: Production Image - A slim, optimized image for production
FROM python:3.10-slim AS production

WORKDIR /code

# Create a non-root user
RUN groupadd -r appgroup && useradd --no-log-init -r -g appgroup appuser

# Copy installed packages, executables and application code from the builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /opt/poetry/bin /usr/local/bin
COPY --from=builder /code/pyproject.toml /code/
COPY ./app /code/app

# Set ownership for the app directory and celery state directory
RUN mkdir -p /var/run/celery && chown -R appuser:appgroup /code /var/run/celery

USER appuser

EXPOSE 8000

# The entrypoint is now app.main:app
# Using "*" for forwarded-allow-ips is more robust in container environments
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
