#!/bin/bash
echo "Debug: Environment variables"
echo "DB_USER=$DB_USER"
echo "DB_HOST=$DB_HOST"
echo "DB_PORT=$DB_PORT"
echo "DB_NAME=$DB_NAME"
echo "PROJECT_ID=$PROJECT_ID"
echo "DB_SECRET_ID=$DB_SECRET_ID"
echo "STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY"

echo "REDIS_HOST=$REDIS_HOST"
echo "REDIS_PORT=$REDIS_PORT"
echo "REDIS_DB=$REDIS_DB"
echo "REDIS_PASSWORD=$REDIS_PASSWORD"

echo "LOG_LEVEL=$LOG_LEVEL"
echo "Debug: Starting Cloud SQL Proxy"
/usr/local/bin/cloud_sql_proxy supple-defender-458912-a2:us-central1:backend-postgres-dev --port 5432 --private-ip --debug > /app/proxy.log 2>&1 &
PROXY_PID=$!

# Poll for proxy readiness with timeout
TIMEOUT=30
COUNT=0
while ! ss -tuln | grep -q ":5432"; do
    if [ $COUNT -ge $TIMEOUT ]; then
        echo "Error: Cloud SQL Proxy failed to listen on port 5432 within $TIMEOUT seconds"
        cat /app/proxy.log
        exit 1
    fi
    if ! ps -p $PROXY_PID > /dev/null; then
        echo "Error: Cloud SQL Proxy process (PID: $PROXY_PID) terminated"
        cat /app/proxy.log
        exit 1
    fi
    echo "Debug: Waiting for Cloud SQL Proxy to start on port 5432..."
    sleep 1
    COUNT=$((COUNT + 1))
done

echo "Debug: Cloud SQL Proxy is running (PID: $PROXY_PID) and listening on port 5432"
echo "Debug: Starting main.py"
exec python3 main.py