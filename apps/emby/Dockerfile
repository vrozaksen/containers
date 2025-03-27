FROM docker.io/library/debian:bookworm-slim

ARG TARGETPLATFORM
ARG VERSION

ENV DEBIAN_FRONTEND=noninteractive \
    TZ="Etc/UTC" \
    EMBY_DATA="/config" \
    UMASK="002"

# Install minimal runtime dependencies
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

# Create emby user and config directory
RUN groupadd -r emby && \
    useradd -r -g emby -d /var/lib/emby -s /usr/sbin/nologin emby && \
    mkdir -p /config /var/lib/emby /var/log/emby && \
    chown -R emby:emby /config /var/lib/emby /var/log/emby

# Install Emby Server with modified post-install
WORKDIR /tmp
RUN case "${TARGETPLATFORM}" in \
        'linux/amd64') ARCH='amd64' ;; \
        'linux/arm64') ARCH='arm64' ;; \
        *) ARCH='amd64' ;; \
    esac && \
    curl -fSL "https://github.com/MediaBrowser/Emby.Releases/releases/download/${VERSION}/emby-server-deb_${VERSION}_${ARCH}.deb" -o emby-server.deb && \
    dpkg --unpack emby-server.deb && \
    sed -i '/systemctl/d' /var/lib/dpkg/info/emby-server.postinst && \
    dpkg --configure -a && \
    apt-get install -fy && \
    rm emby-server.deb && \
    apt-get clean

# Final configuration
RUN echo "EMBY_DATA=/config" > /etc/emby-server.conf

USER emby
WORKDIR /config
VOLUME ["/config"]

ENTRYPOINT ["/opt/emby-server/bin/emby-server", "--programdata", "/config"]

LABEL org.opencontainers.image.source="https://github.com/MediaBrowser/Emby.Releases"
