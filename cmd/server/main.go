package main

import (
	"context"
	"database/sql"
	"github.com/alexlast/bunzap"
	"github.com/felixge/httpsnoop"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/thesammy2010/api.thesammy2010.com/internal"
	pb "github.com/thesammy2010/api.thesammy2010.com/proto/v1/squash"
	squashplayer "github.com/thesammy2010/api.thesammy2010.com/server/v1/squash"
	"github.com/uptrace/bun"
	"github.com/uptrace/bun/dialect/pgdialect"
	"github.com/uptrace/bun/driver/pgdriver"
	"go.uber.org/zap"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/encoding/protojson"
	"net"
	"net/http"
)

var (
	logger = zap.Must(zap.NewProduction())
)

// withLogger This wrapper snoops requests and prints out logs
func withLogger(handler http.Handler) http.Handler {
	return http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		m := httpsnoop.CaptureMetrics(handler, writer, request)
		logger.Info("Request",
			zap.String("method", request.Method),
			zap.Int("status", m.Code),
			zap.String("path", request.URL.Path),
		)
	})
}

// InitModels Used to initialise db models if they don't exist
func initModels(ctx context.Context, db bun.DB) {
	logger.Debug("Initialising models")
	_, err := db.NewCreateTable().Model(&pb.SquashPlayer{}).IfNotExists().Exec(ctx)
	if err != nil {
		logger.Fatal("Failed to initialise model", zap.Error(err))
	}
}

func main() {

	// init logger and config
	logger := zap.Must(zap.NewProduction())
	defer logger.Sync()
	config, err := internal.LoadConfig()
	if err != nil {
		logger.Fatal("Failed to initialise config file", zap.Error(err))
	}

	// connect to db
	pgdb := sql.OpenDB(pgdriver.NewConnector(pgdriver.WithDSN(config.DatabaseURL)))
	db := bun.NewDB(pgdb, pgdialect.New())
	pgdb.SetMaxOpenConns(1)
	db.AddQueryHook(bunzap.NewQueryHook(
		bunzap.QueryHookOptions{
			Logger: logger,
		},
	))

	// init models
	initModels(context.Background(), *db)

	// Reserve port
	lis, err := net.Listen("tcp", ":"+config.GrpcPort)
	if err != nil {
		logger.Fatal("Failed to listen:", zap.Error(err))
	}

	// start gRPC squashPlayerServer
	s := grpc.NewServer()
	// Register SquashPlayer endpoint
	pb.RegisterSquashPlayerServiceServer(s, &squashplayer.PlayerServer{DB: db})
	logger.Info("Serving gRPC", zap.String("Port", config.GrpcPort))
	go func() {
		logger.Fatal("Error serving gRPC", zap.Error(s.Serve(lis)))
	}()

	// Create a client connection to the gRPC squashPlayerServer
	conn, err := grpc.DialContext(
		context.Background(),
		"0.0.0.0:"+config.GrpcPort,
		grpc.WithBlock(),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		logger.Fatal("Failed to dial squashPlayerServer:", zap.Error(err))
	}

	gwmux := runtime.NewServeMux(
		runtime.WithMarshalerOption("application/json+pretty", &runtime.JSONPb{
			MarshalOptions: protojson.MarshalOptions{
				Indent:    "  ",
				Multiline: true,
			},
			UnmarshalOptions: protojson.UnmarshalOptions{
				DiscardUnknown: true,
			},
		}),
	)
	prettier := func(h http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if _, ok := r.URL.Query()["pretty"]; ok {
				r.Header.Set("Accept", "application/json+pretty")
			}
			h.ServeHTTP(w, r)
		})
	}
	// Register Squash Player proxy
	err = pb.RegisterSquashPlayerServiceHandler(context.Background(), gwmux, conn)
	if err != nil {
		logger.Fatal("Failed to register gateway:", zap.Error(err))
	}

	gwServer := &http.Server{
		Addr:    ":" + config.GatewayPort,
		Handler: withLogger(prettier(gwmux)),
	}
	logger.Info("Serving gRPC-Gateway", zap.String("Port", config.GatewayPort))
	logger.Fatal("Error serving gRPC Gateay", zap.Error(gwServer.ListenAndServe()))
}
