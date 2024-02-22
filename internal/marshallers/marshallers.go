package marshallers

import (
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/thesammy2010/api.thesammy2010.com/internal/config"
	"google.golang.org/protobuf/encoding/protojson"
)

var (
	prettier = runtime.WithMarshalerOption("application/json+pretty", &runtime.JSONPb{
		MarshalOptions: protojson.MarshalOptions{
			Indent:    "  ",
			Multiline: true,
		},
		UnmarshalOptions: protojson.UnmarshalOptions{
			DiscardUnknown: true,
		},
	})
	customHeaderResolver = runtime.WithIncomingHeaderMatcher(headerMatcher)
)

func headerMatcher(header string) (string, bool) {
	switch header {
	case "X-User-Id":
		return header, true
	default:
		return runtime.DefaultHeaderMatcher(header)
	}
}

func GetMuxOpts(config config.Config) []runtime.ServeMuxOption {
	opts := []runtime.ServeMuxOption{customHeaderResolver}
	if config.HandlerEnablePrettier {
		opts = append(opts, prettier)
	}
	return opts
}
