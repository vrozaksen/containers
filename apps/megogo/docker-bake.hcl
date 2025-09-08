variable "REGISTRY" {
  default = "ghcr.io"
}

variable "VERSION" {
  default = "latest"
}

group "default" {
  targets = ["megogo"]
}

target "megogo" {
  context = "."
  dockerfile = "Dockerfile"
  tags = [
    "${REGISTRY}/vrozaksen/megogo:${VERSION}",
    "${REGISTRY}/vrozaksen/megogo:latest"
  ]
  # Remove multi-platform for local testing
  # platforms = ["linux/amd64", "linux/arm64"]

  labels = {
    "org.opencontainers.image.title" = "Megogo M3U Generator"
    "org.opencontainers.image.description" = "Docker container for generating M3U playlists from Megogo TV service"
    "org.opencontainers.image.version" = "${VERSION}"
    "org.opencontainers.image.source" = "https://github.com/vrozaksen/containers"
  }
}
