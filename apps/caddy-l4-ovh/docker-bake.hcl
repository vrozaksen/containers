target "docker-metadata-action" {}

variable "APP" {
  default = "caddy-l4-ovh"
}

variable "VERSION" {
  // renovate: datasource=docker depName=caddy
  default = "2.11.3"
}

variable "SOURCE" {
  default = "https://github.com/caddyserver/caddy"
}

group "default" {
  targets = ["image-local"]
}

target "image" {
  inherits = ["docker-metadata-action"]
  args = {
    VERSION = "${VERSION}"
  }
  labels = {
    "org.opencontainers.image.source" = "${SOURCE}"
    "org.opencontainers.image.title" = "caddy-l4-ovh"
    "org.opencontainers.image.description" = "Caddy with layer4 + OVH DNS modules baked in"
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
