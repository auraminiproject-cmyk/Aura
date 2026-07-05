FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services ./services
COPY infra ./infra
COPY data ./data

ENV PYTHONPATH=/app
WORKDIR /app

CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
