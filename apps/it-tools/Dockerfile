ARG VERSION
FROM node:lts-alpine AS build

ARG VERSION

RUN \
  apk add --no-cache curl git \
  && git clone -b ${VERSION} --single-branch https://github.com/CorentinTh/it-tools.git /app \
  && cd /app \
  && corepack enable  \
  && corepack install \
  && corepack prepare pnpm --activate \
  && pnpm install --prefer-offline \
  && pnpm build

  FROM ghcr.io/vrozaksen/caddy-scratch:2.9.1@sha256:c0d60c7e4eb93686187748a687a7b874a198eff0128c409740deaf987f872245
  COPY --chown=1000:1000 --from=build /app/dist/ /app
  CMD ["file-server", "--root", "/app", "--listen", ":8080"]

LABEL org.opencontainers.image.source="https://github.com/CorentinTh/it-tools"