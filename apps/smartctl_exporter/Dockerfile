FROM docker.io/library/alpine:3.21

ARG TARGETPLATFORM
ARG VERSION

RUN apk add smartmontools
RUN wget "https://github.com/prometheus-community/smartctl_exporter/releases/download/v${VERSION}/smartctl_exporter-${VERSION}.linux-${TARGETARCH}.tar.gz" \
  && tar xvzf smartctl_exporter-${VERSION}.linux-${TARGETARCH}.tar.gz \
  && ls -l smartctl_exporter-${VERSION}.linux-${TARGETARCH}.tar.gz \
  && mv smartctl_exporter-${VERSION}.linux-${TARGETARCH}/smartctl_exporter /bin/smartctl_exporter \
  && chmod +x /bin/smartctl_exporter \
  && rm -rf smartctl_exporter*

EXPOSE      9633
USER        nobody
ENTRYPOINT  [ "/bin/smartctl_exporter" ]

LABEL org.opencontainers.image.source="https://github.com/prometheus-community/smartctl_exporter"
