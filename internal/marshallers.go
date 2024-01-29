package internal

import (
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
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
)

func GetMuxOpts(config Config) []runtime.ServeMuxOption {
	var opts []runtime.ServeMuxOption
	if config.HandlerEnablePrettier {
		opts = append(opts, prettier)
	}
	return opts
}
