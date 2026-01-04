# RSS Worker Container for Azure Container Apps
# Always-on worker for reliable RSS feed ingestion

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY worker.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default configuration (override in Container Apps)
ENV FEEDS_PER_CYCLE=10
ENV POLL_INTERVAL_SECONDS=10
ENV FEED_TIMEOUT_SECONDS=30
ENV CIRCUIT_BREAKER_THRESHOLD=3
ENV CIRCUIT_BREAKER_TIMEOUT_MINUTES=30
ENV FEED_COOLDOWN_MINUTES=5

# Expose health check port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the worker
CMD ["python", "worker.py"]
