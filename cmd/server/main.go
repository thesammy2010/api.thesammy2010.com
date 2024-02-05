package main

import (
	"context"
	"database/sql"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/thesammy2010/api.thesammy2010.com/internal/cache"
	"github.com/thesammy2010/api.thesammy2010.com/internal/config"
	"github.com/thesammy2010/api.thesammy2010.com/internal/handlers"
	"github.com/thesammy2010/api.thesammy2010.com/internal/logger"
	"github.com/thesammy2010/api.thesammy2010.com/internal/marshallers"
	pb "github.com/thesammy2010/api.thesammy2010.com/proto/v1/squash"
	squashplayer "github.com/thesammy2010/api.thesammy2010.com/server/v1/squash"
	"github.com/uptrace/bun"
	"github.com/uptrace/bun/dialect/pgdialect"
	"github.com/uptrace/bun/driver/pgdriver"
	"github.com/uptrace/bun/extra/bundebug"
	"go.uber.org/zap"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"net"
	"net/http"
	"time"
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

	cfg, err := config.LoadConfig()
	if err != nil {
		logger.Fatal("Failed to initialise config file", zap.Error(err))
	}

	// connect to db
	pgdb := sql.OpenDB(pgdriver.NewConnector(
		pgdriver.WithDSN(cfg.DatabaseURL),
		pgdriver.WithTimeout(5*time.Second),
		pgdriver.WithDialTimeout(5*time.Second),
		pgdriver.WithReadTimeout(5*time.Second),
		pgdriver.WithWriteTimeout(5*time.Second),
	))
	db := bun.NewDB(pgdb, pgdialect.New())
	pgdb.SetMaxOpenConns(1)
	//db.AddQueryHook(bunzap.NewQueryHook(
	//	bunzap.QueryHookOptions{
	//		Logger: logger.Logger,
	//	},
	//))
	bundebug.NewQueryHook(bundebug.WithEnabled(false))

	// init models
	initModels(context.Background(), *db)

	// Reserve port
	lis, err := net.Listen("tcp", ":"+cfg.GrpcPort)
	if err != nil {
		logger.Fatal("Failed to listen:", zap.Error(err))
	}

	// start gRPC squashPlayerServer
	s := grpc.NewServer()
	// Register SquashPlayer endpoint
	pb.RegisterSquashPlayerServiceServer(s, &squashplayer.PlayerServer{DB: db, Cache: cache.NewCache(cfg.CacheDefaultExpiration, cfg.CachePurgeTime)})
	logger.Info("Serving gRPC", zap.String("Port", cfg.GrpcPort))
	go func() {
		logger.Fatal("Error serving gRPC", zap.Error(s.Serve(lis)))
	}()

	// Create a client connection to the gRPC squashPlayerServer
	conn, err := grpc.DialContext(
		context.Background(),
		"0.0.0.0:"+cfg.GrpcPort,
		grpc.WithBlock(),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		logger.Fatal("Failed to dial squashPlayerServer:", zap.Error(err))
	}

	gwmux := runtime.NewServeMux(marshallers.GetMuxOpts(cfg)...)
	// Register Squash Player proxy
	err = pb.RegisterSquashPlayerServiceHandler(context.Background(), gwmux, conn)
	if err != nil {
		logger.Fatal("Failed to register gateway:", zap.Error(err))
	}

	gwServer := &http.Server{
		Addr:         ":" + cfg.GatewayPort,
		Handler:      handlers.HttpHandler(gwmux, cfg),
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
	}
	logger.Info("Serving gRPC-Gateway", zap.String("Port", cfg.GatewayPort))
	logger.Fatal("Error serving gRPC Gateay", zap.Error(gwServer.ListenAndServe()))
}
