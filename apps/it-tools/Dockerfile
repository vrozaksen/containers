ARG VERSION
FROM node:lts-alpine AS build

ARG VERSION
ARG CHANNEL
ARG TARGETPLATFORM
ARG TARGETARCH
ARG TARGETOS

LABEL dev.vrozaksen.image.target_platform=$TARGETPLATFORM
LABEL dev.vrozaksen.image.target_architecture=$TARGETARCH
LABEL dev.vrozaksen.image.target_os=$TARGETOS
LABEL org.opencontainers.image.source="https://github.com/CorentinTh/it-tools"

RUN \
  apk add --no-cache curl git jq \
  && git clone -b v$VERSION --single-branch https://github.com/CorentinTh/it-tools.git /app \
  && cd /app \
  && corepack enable  \
  && corepack prepare pnpm@latest --activate \
  && pnpm install --prefer-offline \
  && pnpm build

  FROM ghcr.io/vrozaksen/caddy-scratch:2.9.1@sha256:637f10bef3516b68de5a7cf1f4cd36b6d6417e6c8d7dd16d22f8845e610c9fdc
  COPY --chown=1000:1000 --from=build /app/dist/ /app
  CMD ["file-server", "--root", "/app", "--listen", ":8080"]
