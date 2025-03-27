FROM docker.io/library/debian:bookworm-slim

ARG TARGETPLATFORM
ARG VENDOR
ARG VERSION

ENV DEBIAN_FRONTEND=noninteractive \
    TZ="Etc/UTC" \
    LANGUAGE="en_US.UTF-8" \
    LANG="en_US.UTF-8" \
    EMBY_DATA="/config" \
    DOTNET_SYSTEM_GLOBALIZATION_INVARIANT="1" \
    UMASK="002" \
    ASPNETCORE_URLS="http://+:8096"

# Install dependencies
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

# Final configuration
RUN echo "EMBY_DATA=/config" > /etc/emby-server.conf

USER emby
WORKDIR /config
VOLUME ["/config"]

EXPOSE 8096/tcp 8920/tcp 7359/udp 1900/udp

ENTRYPOINT ["/opt/emby-server/bin/emby-server"]
