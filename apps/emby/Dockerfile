FROM docker.io/library/debian:bookworm-slim

ARG TARGETPLATFORM
ARG VERSION

ENV DEBIAN_FRONTEND=noninteractive \
    TZ="Etc/UTC" \
    UMASK="002" \
    EMBY_DATA="/config"

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        ffmpeg \
        libsqlite3-0 \
        libssl3 \
        libicu72 \
        fontconfig \
        libfreetype6 \
        libass9 \
    && rm -rf /var/lib/apt/lists/*

# Install Emby
WORKDIR /tmp
RUN case "${TARGETPLATFORM}" in \
        'linux/amd64') ARCH='amd64' ;; \
        'linux/arm64') ARCH='arm64' ;; \
        *) ARCH='amd64' ;; \
    esac && \
    curl -fSL "https://github.com/MediaBrowser/Emby.Releases/releases/download/${VERSION}/emby-server-deb_${VERSION}_${ARCH}.deb" -o emby-server.deb && \
    dpkg --unpack emby-server.deb && \
    rm -rf /usr/lib/systemd /var/lib/dpkg/info/emby-server.postinst && \
    dpkg --configure -a && \
    apt-get install -fy && \
    rm emby-server.deb && \
    apt-get clean

# Minimal config
RUN echo "EMBY_DATA=${EMBY_DATA}" > /etc/emby-server.conf

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/config"]
RUN chown -R nobody:nogroup /config

USER nobody:nogroup

ENTRYPOINT ["/entrypoint.sh"]

LABEL org.opencontainers.image.source="https://github.com/MediaBrowser/Emby.Releases"
