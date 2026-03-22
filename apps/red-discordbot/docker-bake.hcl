target "docker-metadata-action" {}

variable "APP" {
  default = "red-discordbot"
}

variable "VERSION" {
  // renovate: datasource=pypi depName=Red-DiscordBot
  default = "3.5.24"
}

group "default" {
  targets = ["image-local"]
}

variable "SOURCE" {
  default = "https://github.com/Cog-Creators/Red-DiscordBot"
}

target "image" {
  inherits = ["docker-metadata-action"]
  args = {
    VERSION = "${VERSION}"
  }
  labels = {
    "org.opencontainers.image.source" = "${SOURCE}"
    "org.opencontainers.image.title" = "Red-DiscordBot"
    "org.opencontainers.image.description" = "Custom rootless Red-DiscordBot with JSON and PostgreSQL backend support"
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
