FROM python:3.11 AS builder
LABEL version="1.0"

# Install poetry
RUN pip install poetry==2.1.3
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN ls -la
RUN touch README.md
RUN poetry install --only main --no-root && rm -rf $POETRY_CACHE_DIR

FROM python:3.11-slim AS runtime

# Install necessary utilities
RUN apt-get update && apt-get install -y \
    curl \
    wget 
RUN rm -rf /var/lib/apt/lists/*

# Copy dependencies into virtual environment
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy main application
WORKDIR /app
COPY rtci ./rtci
COPY main.py ./
RUN mkdir -p ./log/
RUN mkdir -p ./cache/

# Copy start scripts
COPY docker/docker-entrypoint.sh /usr/local/bin/

# Setup container parameters
EXPOSE 8000
VOLUME ["/app/log/"]

# Create user with the name poetry
RUN groupadd -g 1500 fastapi && \
    useradd -m -u 1500 -g fastapi fastapi
RUN chown -R fastapi:fastapi /app
USER fastapi
WORKDIR /app

# Setup main directory and run server
ENTRYPOINT ["docker-entrypoint.sh"]
