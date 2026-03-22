# syntax=docker/dockerfile:1

FROM docker.io/library/alpine:3.23 AS fetcher

ARG VERSION
ARG TARGETARCH

RUN \
    apk add --no-cache curl \
    && \
    curl -fsSL -o /Lavalink.jar \
        "https://github.com/lavalink-devs/Lavalink/releases/download/${VERSION}/Lavalink.jar"

FROM docker.io/library/eclipse-temurin:21-jre-alpine

ENV LANG="C.UTF-8"

USER root

RUN \
    apk add --no-cache \
        bash \
        ca-certificates \
        catatonit \
        curl \
        libgcc \
        su-exec \
        tzdata \
    && \
    mkdir -p /app/defaults /data \
    && chown -R nobody:nogroup /app /data \
    && chmod -R 755 /app /data

COPY --from=fetcher /Lavalink.jar /app/Lavalink.jar
COPY defaults/ /app/defaults/
COPY entrypoint.sh /entrypoint.sh

USER nobody:nogroup
WORKDIR /data
VOLUME ["/data"]

EXPOSE 2333

ENTRYPOINT ["/usr/bin/catatonit", "--", "/entrypoint.sh"]
