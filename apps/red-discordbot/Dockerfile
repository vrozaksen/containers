# syntax=docker/dockerfile:1

FROM docker.io/library/python:3.11-slim-bookworm AS builder

ARG VERSION

ENV PYTHONDONTWRITEBYTECODE=1

RUN \
    apt-get update \
    && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        build-essential \
        git \
        libpq-dev \
        pkg-config \
    && \
    python -m venv /opt/venv \
    && \
    . /opt/venv/bin/activate \
    && \
    pip install --no-cache-dir \
        wheel \
        "Red-DiscordBot[postgres]==${VERSION}" \
    && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

FROM docker.io/library/python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND="noninteractive" \
    HOME="/data" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

USER root

RUN \
    apt-get update \
    && \
    apt-get install -y --no-install-recommends --no-install-suggests \
        ca-certificates \
        catatonit \
        curl \
        git \
        gosu \
        jq \
        libpq5 \
        tzdata \
    && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && \
    mkdir -p /data \
    && chown -R nobody:nogroup /data \
    && chmod -R 755 /data

COPY --from=builder /opt/venv /opt/venv
COPY . /

USER nobody:nogroup
WORKDIR /data
VOLUME ["/data"]

ENTRYPOINT ["/usr/bin/catatonit", "--", "/entrypoint.sh"]
