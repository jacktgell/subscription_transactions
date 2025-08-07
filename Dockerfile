FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-dev \
    libpq-dev \
    gcc \
    wget \
    build-essential \
    iproute2 \
    && wget https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.18.0/cloud-sql-proxy.linux.amd64 -O /usr/local/bin/cloud_sql_proxy \
    && chmod +x /usr/local/bin/cloud_sql_proxy \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY main.py /app/main.py
COPY resources/ /app/resources/
COPY update_active_status/ /app/update_active_status/
COPY update_commision_transactions/ /app/update_commision_transactions/
COPY update_redis/ /app/update_redis/

RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'set -e' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Start Cloud SQL Proxy' >> /app/start.sh && \
    echo 'cloud_sql_proxy -instances=${CLOUD_SQL_CONNECTION_NAME}=tcp:5433 &' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Wait for proxy to initialize' >> /app/start.sh && \
    echo 'sleep 10' >> /app/start.sh && \
    echo '' >> /app/start.sh && \
    echo '# Run the main application' >> /app/start.sh && \
    echo 'python3 main.py' >> /app/start.sh

RUN useradd -m appuser \
    && chown -R appuser:appuser /app \
    && chmod +x /app/start.sh \
    && chmod -R 755 /app

USER appuser

ENV PYTHONUNBUFFERED=1 \
    LD_LIBRARY_PATH=/usr/lib \
    GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
    CLOUD_SQL_CONNECTION_NAME=supple-defender-458912-a2:asia-southeast1:neurakinetic

CMD ["./start.sh"]