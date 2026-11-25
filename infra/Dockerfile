# Gnana app image (dev). Production will get a gunicorn + nginx variant later.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first so this layer is cached across rebuilds.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application (respects .dockerignore).
COPY . .

# Entry point waits for Postgres, migrates, seeds, then execs the CMD.
# Called via `sh` so no executable bit is required (host bind mounts can
# shadow a chmod'd COPY of this file).
RUN chmod +x infra/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["sh", "/app/infra/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
