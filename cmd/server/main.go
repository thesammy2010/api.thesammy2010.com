package main

import (
	"context"
	"database/sql"
	"github.com/alexlast/bunzap"
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
	"net"
	"net/http"
	"time"
)

var (
	logger = zap.Must(zap.NewProduction())
)

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
	pgdb := sql.OpenDB(pgdriver.NewConnector(
		pgdriver.WithDSN(config.DatabaseURL),
		pgdriver.WithTimeout(5*time.Second),
		pgdriver.WithDialTimeout(5*time.Second),
		pgdriver.WithReadTimeout(5*time.Second),
		pgdriver.WithWriteTimeout(5*time.Second),
	))
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

	gwmux := runtime.NewServeMux(internal.GetMuxOpts(config)...)
	// Register Squash Player proxy
	err = pb.RegisterSquashPlayerServiceHandler(context.Background(), gwmux, conn)
	if err != nil {
		logger.Fatal("Failed to register gateway:", zap.Error(err))
	}

	gwServer := &http.Server{
		Addr:         ":" + config.GatewayPort,
		Handler:      internal.HttpHandler(gwmux, config),
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
	}
	logger.Info("Serving gRPC-Gateway", zap.String("Port", config.GatewayPort))
	logger.Fatal("Error serving gRPC Gateay", zap.Error(gwServer.ListenAndServe()))
}
