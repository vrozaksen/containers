FROM docker.io/library/alpine:3.21

ARG VERSION
ARG CHANNEL
ARG TARGETPLATFORM
ARG TARGETARCH
ARG TARGETOS

LABEL dev.vrozaksen.image.target_platform=$TARGETPLATFORM
LABEL dev.vrozaksen.image.target_architecture=$TARGETARCH
LABEL dev.vrozaksen.image.target_os=$TARGETOS
LABEL org.opencontainers.image.source="https://github.com/networkupstools/nut"

RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories

RUN apk add --no-cache nut

# fix some missing links to .so files, which are required to run 'nut-scanner' utility
RUN find /usr/lib/ -type f -name 'libusb*' -exec ln -sf {} /usr/lib/libusb-1.0.so \; || false
RUN find /usr/lib/ -type f -name 'libnetsnmp*' -exec ln -sf {} /usr/lib/libnetsnmp.so \; || false
RUN find /usr/lib/ -type f -name 'libupsclient*' -exec ln -sf {} /usr/lib/libupsclient.so \; || false
RUN find /usr/lib/ -type f -name 'libneon*' -exec ln -sf {} /usr/lib/libneon.so \; || false

COPY ./entrypoint.sh /entrypoint.sh

RUN chmod 700 /entrypoint.sh

RUN mkdir -p /var/run/nut && \
    chown nut:nut /var/run/nut && \
    chmod 700 /var/run/nut

WORKDIR /config

EXPOSE 3493
ENTRYPOINT ["/entrypoint.sh"]
