FROM docker.io/library/alpine:rolling@sha256:36eada10cae882bb8c8dfeea701cb8740210cb556e0931d777467c776af3b54a

ARG TARGETPLATFORM
ARG VERSION
ARG CHANNEL
ARG TARGETARCH
ENV TARGETARCH=${TARGETARCH:-amd64}

LABEL dev.vrozaksen.image.target_platform=$TARGETPLATFORM
LABEL dev.vrozaksen.image.target_architecture=$TARGETARCH
LABEL dev.vrozaksen.image.target_os=$TARGETOS
LABEL org.opencontainers.image.source="https://github.com/kubernetes/kubectl"

#hadolint ignore=DL3018
RUN apk add --no-cache ca-certificates openssl
#hadolint ignore=DL3018,DL3059
RUN \
    curl -fsSL -o /usr/local/bin/kubectl "https://dl.k8s.io/release/v${VERSION}/bin/linux/${TARGETARCH}/kubectl" \
    && chmod +x /usr/local/bin/kubectl

USER kah
CMD [ "/usr/local/bin/kubectl" ]
