FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Warsaw

RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install only required Python dependencies
RUN pip install --no-cache-dir requests

# Create application directory and user
WORKDIR /app
RUN groupadd -r megogo && useradd -r -g megogo megogo

# Copy only needed application files
COPY --chown=megogo:megogo apps/megogo/megogo_m3u.py ./
COPY --chown=megogo:megogo apps/megogo/entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Create data directory for cache
RUN mkdir -p /app/data && chown -R megogo:megogo /app/data

# Switch to non-root user
USER megogo

# Expose port for M3U server
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/status || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
