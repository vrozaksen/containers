FROM docker.io/library/debian:bookworm-slim

ARG TARGETPLATFORM="linux/amd64"
ARG VERSION="4.8.11.0"

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

# Create user and directories
RUN groupadd -r emby && \
    useradd -r -g emby -d /config -s /usr/sbin/nologin emby && \
    mkdir -p /config /var/lib/emby && \
    chown -R emby:emby /config /var/lib/emby && \
    ln -s /config /var/lib/emby

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

# Final config
RUN echo "EMBY_DATA=/config" > /etc/emby-server.conf

USER emby
WORKDIR /config
VOLUME ["/config"]

ENTRYPOINT ["/opt/emby-server/bin/EmbyServer", "--programdata", "/config"]

LABEL org.opencontainers.image.source="https://github.com/MediaBrowser/Emby.Releases"
