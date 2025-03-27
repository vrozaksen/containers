FROM docker.io/library/debian:bookworm-slim

ARG TARGETPLATFORM
ARG VENDOR
ARG VERSION

ENV DEBIAN_FRONTEND=noninteractive \
    TZ="Etc/UTC" \
    LANGUAGE="en_US.UTF-8" \
    LANG="en_US.UTF-8" \
    EMBY_DATA="/config" \
    UMASK="002" \
    ASPNETCORE_URLS="http://+:8096" \
    GOSS_WAIT_OPTS="-r 60s -s 5s" \
    GOSS_SLEEP="15s"

# Install dependencies and configure locale
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        locales \
        ca-certificates \
        curl \
        ffmpeg \
        libsqlite3-0 \
        procps \
        libicu72 \
        libssl3 \
        && \
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create emby user
RUN groupadd -r emby && \
    useradd -r -g emby -d /var/lib/emby -s /usr/sbin/nologin emby && \
    mkdir -p /config && \
    chown emby:emby /config

# Install Emby Server
WORKDIR /tmp
RUN case "${TARGETPLATFORM}" in \
        'linux/amd64') export ARCH='amd64' ;; \
        'linux/arm64') export ARCH='arm64' ;; \
        'linux/arm/v7') export ARCH='armhf' ;; \
    esac && \
    curl -fsSL "https://github.com/MediaBrowser/Emby.Releases/releases/download/${VERSION}/emby-server-deb_${VERSION}_${ARCH}.deb" -o emby-server.deb && \
    dpkg --unpack emby-server.deb && \
    rm -f /var/lib/dpkg/info/emby-server.postinst && \
    dpkg --configure -a && \
    apt-get install -fy && \
    rm emby-server.deb && \
    printf "UpdateMethod=docker\nVersion=%s\nPackageAuthor=[%s](https://github.com/%s)\n" "${VERSION}" "${VENDOR}" "${VENDOR}" > /package_info && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/*

# Final configuration with health check
RUN echo "EMBY_DATA=/config" > /etc/emby-server.conf && \
    echo "#!/bin/sh" > /healthcheck.sh && \
    echo "curl -fs http://localhost:8096/System/Info/Public || exit 1" >> /healthcheck.sh && \
    chmod +x /healthcheck.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /healthcheck.sh

USER emby
WORKDIR /config
VOLUME ["/config"]

EXPOSE 8096/tcp 8920/tcp 7359/udp 1900/udp

ENTRYPOINT ["/opt/emby-server/bin/emby-server"]
