FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Warsaw

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    tzdata \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    requests \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    jinja2

# Create application directory and user
WORKDIR /app
RUN groupadd -r megogo && useradd -r -g megogo megogo

# Copy application files
COPY --chown=megogo:megogo . /app/

# Create data directory for configuration and playlists
RUN mkdir -p /app/data && chown -R megogo:megogo /app/data

# Make scripts executable
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER megogo

# Expose port for web interface
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
