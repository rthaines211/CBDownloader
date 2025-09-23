FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY cbdownloader /app/cbdownloader

RUN pip install --no-cache-dir ".[web]"

RUN mkdir -p /data

EXPOSE 8000
VOLUME ["/data"]

CMD ["python", "-m", "cbdownloader.webserver", "--host", "0.0.0.0", "--port", "8000", "--output-dir", "/data"]
