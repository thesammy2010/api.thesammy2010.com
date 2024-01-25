package main

import (
	"context"
	"database/sql"
	"github.com/uptrace/bun"
	"github.com/uptrace/bun/dialect/pgdialect"
	"github.com/uptrace/bun/driver/pgdriver"
	"github.com/uptrace/bun/extra/bundebug"
	"log"

	m "github.com/thesammy2010/api.thesammy2010.com/server/v1/squash"

	"os"
)

// main method to run for restarting
func main() {
	ctx := context.Background()
	pgdb := sql.OpenDB(pgdriver.NewConnector(pgdriver.WithDSN(os.Getenv("DATABASE_URL"))))
	db := bun.NewDB(pgdb, pgdialect.New())
	pgdb.SetMaxOpenConns(1)
	db.AddQueryHook(bundebug.NewQueryHook(
		bundebug.WithVerbose(true),
		bundebug.FromEnv("BUNDEBUG"),
	))
	resetModels(ctx, *db)
}

// resetModels Used to recreate tables
func resetModels(ctx context.Context, db bun.DB) {
	// Reset Create Squash Player model
	err := db.ResetModel(ctx, &m.DatabaseModel{})
	if err != nil {
		log.Fatalf("Failed to reset model %+v, ", err)
	}
}
