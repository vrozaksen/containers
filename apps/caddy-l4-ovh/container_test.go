package main

import (
	"context"
	"testing"

	"github.com/vrozaksen/containers/testhelpers"
)

func TestCaddyLayer4Module(t *testing.T) {
	ctx := context.Background()
	image := testhelpers.GetTestImage("ghcr.io/vrozaksen/caddy-l4-ovh:rolling")
	testhelpers.TestCommandSucceeds(t, ctx, image, nil,
		"sh", "-c", "caddy list-modules | grep -q '^layer4'")
}

func TestCaddyOvhDNSModule(t *testing.T) {
	ctx := context.Background()
	image := testhelpers.GetTestImage("ghcr.io/vrozaksen/caddy-l4-ovh:rolling")
	testhelpers.TestCommandSucceeds(t, ctx, image, nil,
		"sh", "-c", "caddy list-modules | grep -q '^dns.providers.ovh'")
}
