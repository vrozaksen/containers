target "docker-metadata-action" {}

variable "APP" {
  default = "megogo"
}

variable "VERSION" {
  default = "latest"
}

group "default" {
  targets = ["image-local"]
}

variable "SOURCE" {
  default = "https://github.com/vrozaksen/containers"
}

target "image" {
  inherits = ["docker-metadata-action"]
  args = {
    VERSION = "${VERSION}"
  }
  labels = {
    "org.opencontainers.image.title" = "Megogo M3U Generator"
    "org.opencontainers.image.description" = "Docker container for generating M3U playlists from Megogo TV service"
    "org.opencontainers.image.version" = "${VERSION}"
    "org.opencontainers.image.source" = "${SOURCE}"
  }
}

target "image-local" {
  inherits = ["image"]
  output = ["type=docker"]
  tags = ["${APP}:${VERSION}"]
}

target "image-all" {
  inherits = ["image"]
  platforms = [
    "linux/amd64",
    "linux/arm64"
  ]
}
