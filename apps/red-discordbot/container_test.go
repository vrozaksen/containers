package main

import (
	"context"
	"testing"

	"github.com/vrozaksen/containers/testhelpers"
)

func TestRedBotVersion(t *testing.T) {
	ctx := context.Background()
	image := testhelpers.GetTestImage("ghcr.io/vrozaksen/red-discordbot:rolling")
	testhelpers.TestCommandSucceeds(t, ctx, image, nil, "redbot", "--version")
}

func TestDataDirExists(t *testing.T) {
	ctx := context.Background()
	image := testhelpers.GetTestImage("ghcr.io/vrozaksen/red-discordbot:rolling")
	testhelpers.TestCommandSucceeds(t, ctx, image, nil, "test", "-d", "/data")
}
