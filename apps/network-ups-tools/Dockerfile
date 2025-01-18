FROM ghcr.io/jr0dd/ubuntu-jammy:rolling@sha256:6fa96cfa6bd030baa8c6e0d104e7080312871c2daaec7e2702d1e890915a33b2

ARG VERSION
ARG CHANNEL
ARG TARGETPLATFORM
ARG TARGETARCH
ARG TARGETOS

LABEL dev.vrozaksen.image.target_platform=$TARGETPLATFORM
LABEL dev.vrozaksen.image.target_architecture=$TARGETARCH
LABEL dev.vrozaksen.image.target_os=$TARGETOS
LABEL org.opencontainers.image.source="https://github.com/networkupstools/nut"

# hadolint ignore=DL3008,DL3015,SC2086
RUN \
  apt-get -qq update \
  && apt-get -qq install -y --no-install-recommends \
    nut-server nut-client \
  && apt-get clean \
  && rm -rf \
    /tmp/* \
    /var/lib/apt/lists/ \
    /var/tmp/*


EXPOSE 3493

COPY ./entrypoint.sh /entrypoint.sh

USER root
WORKDIR /config

CMD ["/entrypoint.sh"]
