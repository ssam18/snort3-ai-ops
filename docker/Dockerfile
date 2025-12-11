FROM python:3.11-slim

LABEL maintainer="Snort3-AI-Ops Contributors"
LABEL description="AI-Ops engine for Snort3 intrusion prevention system"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libzmq3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/reports /app/models

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SNORT3_AIOPS_HOME=/app

# Expose ports
EXPOSE 8000 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the application
CMD ["python", "main.py", "start", "--config", "config/config.yaml"]
