# syntax=docker/dockerfile:1
ARG VERSION

FROM docker.io/caddy:${VERSION}-builder AS builder
ARG VERSION
RUN xcaddy build v${VERSION} \
    --with github.com/mholt/caddy-l4 \
    --with github.com/caddy-dns/ovh

FROM docker.io/caddy:${VERSION}
COPY --from=builder /usr/bin/caddy /usr/bin/caddy

LABEL org.opencontainers.image.source="https://github.com/caddyserver/caddy" \
      org.opencontainers.image.title="caddy-l4-ovh" \
      org.opencontainers.image.description="Caddy with layer4 + OVH DNS modules baked in"
