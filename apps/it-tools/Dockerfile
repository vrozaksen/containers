ARG VERSION
FROM node:lts-alpine AS build
ARG VERSION

RUN \
  apk add --no-cache curl git \
  && git clone -b v${VERSION} --single-branch https://github.com/CorentinTh/it-tools.git /app \
  && cd /app \
  && npm install -g corepack@latest \
  && corepack enable  \
  && corepack prepare pnpm@latest --activate \
  && pnpm install --prefer-offline \
  && pnpm build

FROM ghcr.io/vrozaksen/caddy-scratch:2.9.1@sha256:6a64a4f5ffe3bf24312cf00c7e3b7734784a0c4963d421f84b6a8a72aea24ce7

COPY --chown=1000:1000 --from=build /app/dist/ /app
CMD ["file-server", "--root", "/app", "--listen", ":8080"]
