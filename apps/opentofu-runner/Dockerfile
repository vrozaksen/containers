FROM docker.io/library/alpine:3.21 AS opentofu

ARG VERSION
ARG TARGETPLATFORM

RUN \
    apk add --no-cache \
        bash \
        curl \
    && \
    case "${TARGETPLATFORM}" in \
        'linux/amd64') \
            export ARCH='amd64'; \
        ;; \
        'linux/arm64') \
            export ARCH='arm64'; \
        ;; \
    esac \
    && curl -fsSL -o /tmp/tofu_${VERSION}_linux_${ARCH}.tar.gz "https://github.com/opentofu/opentofu/releases/download/v${VERSION}/tofu_${VERSION}_linux_${ARCH}.tar.gz" \
    && tar -xzvf /tmp/tofu_${VERSION}_linux_${ARCH}.tar.gz -C /tmp \
    && chmod +x /tmp/tofu

LABEL org.opencontainers.image.source="https://github.com/opentofu/opentofu"

FROM ghcr.io/flux-iac/tf-runner:v0.16.0-rc.5 AS runner

USER root

COPY --from=opentofu --chown=65532:65532 /tmp/tofu /usr/local/bin/terraform

USER 65532:65532

LABEL org.opencontainers.image.source="https://github.com/opentofu/opentofu"