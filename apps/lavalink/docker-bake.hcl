target "docker-metadata-action" {}

variable "APP" {
  default = "lavalink"
}

variable "VERSION" {
  // renovate: datasource=github-releases depName=lavalink-devs/Lavalink
  default = "4.2.2"
}

group "default" {
  targets = ["image-local"]
}

variable "SOURCE" {
  default = "https://github.com/lavalink-devs/Lavalink"
}

target "image" {
  inherits = ["docker-metadata-action"]
  args = {
    VERSION = "${VERSION}"
  }
  labels = {
    "org.opencontainers.image.source" = "${SOURCE}"
    "org.opencontainers.image.title" = "Lavalink"
    "org.opencontainers.image.description" = "Lavalink audio server for Discord bots"
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
