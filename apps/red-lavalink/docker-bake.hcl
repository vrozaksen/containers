target "docker-metadata-action" {}

variable "APP" {
  default = "red-lavalink"
}

variable "VERSION" {
  // renovate: datasource=github-releases depName=Cog-Creators/Lavalink-Jars versioning=loose
  default = "3.7.13+red.5"
}

group "default" {
  targets = ["image-local"]
}

variable "SOURCE" {
  default = "https://github.com/Cog-Creators/Lavalink-Jars"
}

target "image" {
  inherits = ["docker-metadata-action"]
  args = {
    VERSION = "${VERSION}"
  }
  labels = {
    "org.opencontainers.image.source" = "${SOURCE}"
    "org.opencontainers.image.title" = "Red-Lavalink"
    "org.opencontainers.image.description" = "Lavalink v3 server for Red-DiscordBot (Cog-Creators fork)"
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
