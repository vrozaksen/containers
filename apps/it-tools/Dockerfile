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
  apk add --no-cache curl git \
  && git clone -b v${VERSION} --single-branch https://github.com/CorentinTh/it-tools.git /app \
  && cd /app \
  && corepack enable  \
  && corepack install \
  && corepack prepare pnpm --activate \
  && pnpm install --prefer-offline \
  && pnpm build

  FROM ghcr.io/vrozaksen/caddy-scratch:2.9.1@sha256:3b32213a571aa2a50903c1bb9d1fe550888acaf2e75929f52a534005ac192e9d
  COPY --chown=1000:1000 --from=build /app/dist/ /app
  CMD ["file-server", "--root", "/app", "--listen", ":8080"]
