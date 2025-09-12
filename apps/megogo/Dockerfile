FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Warsaw

RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install required Python dependencies
RUN pip install --no-cache-dir requests

# Create application directory and user
WORKDIR /app
RUN groupadd -r megogo && useradd -r -g megogo megogo

# Copy application files
COPY megogo_m3u.py /app/
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Create data directory for configuration and cache
RUN mkdir -p /app/data && chown -R megogo:megogo /app

# Switch to non-root user
USER megogo

# Expose port for M3U server
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/status || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
