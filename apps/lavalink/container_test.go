package main

import (
	"context"
	"testing"

	"github.com/vrozaksen/containers/testhelpers"
)

func TestLavalinkHTTP(t *testing.T) {
	ctx := context.Background()
	image := testhelpers.GetTestImage("ghcr.io/vrozaksen/lavalink:rolling")
	// Lavalink 4.x requires Authorization header; 401 confirms server is running
	testhelpers.TestHTTPEndpoint(t, ctx, image, testhelpers.HTTPTestConfig{
		Port:       "2333",
		Path:       "/version",
		StatusCode: 401,
	}, nil)
}
