package main

import (
	"context"
	"database/sql"
	"github.com/alexlast/bunzap"
	"github.com/thesammy2010/api.thesammy2010.com/internal"
	pb "github.com/thesammy2010/api.thesammy2010.com/server/v1/squash"
	"github.com/uptrace/bun"
	"github.com/uptrace/bun/dialect/pgdialect"
	"github.com/uptrace/bun/driver/pgdriver"
	"github.com/uptrace/bun/extra/bundebug"
	"go.uber.org/zap"
)

var (
	logger = zap.Must(zap.NewProduction())
)

// main method to run for restarting
func main() {
	// read config and set up logging
	ctx := context.Background()
	config, err := internal.LoadConfig()
	if err != nil {
		logger.Fatal("Failed to initialise config file", zap.Error(err))
	}

	// open connection to db
	pgdb := sql.OpenDB(pgdriver.NewConnector(pgdriver.WithDSN(config.DatabaseURL)))
	db := bun.NewDB(pgdb, pgdialect.New())
	pgdb.SetMaxOpenConns(1)
	bundebug.NewQueryHook(bundebug.WithVerbose(true))
	db.AddQueryHook(bunzap.NewQueryHook(bunzap.QueryHookOptions{
		Logger: logger,
	}))
	logger.Info("Database connection successfully established")
	resetModels(ctx, *db)
}

// resetModels Used to recreate tables
func resetModels(ctx context.Context, db bun.DB) {
	// Reset Create Squash Player model
	logger.Info("Resetting `squash_player`")
	err := db.ResetModel(ctx, &pb.SquashPlayer{})
	if err != nil {
		logger.Fatal("Failed to reset model: %v, ", zap.Error(err))
	}
	logger.Info("All resets complete successfully")
}
