FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services ./services
ENV PYTHONPATH=/app
ENV STORAGE_BACKEND=local
ENV STORAGE_LOCAL_PATH=/app/data/storage
ENV DATABASE_URL=sqlite+aiosqlite:////app/data/fashionai.db

RUN mkdir -p /app/data/storage

EXPOSE 7860
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
