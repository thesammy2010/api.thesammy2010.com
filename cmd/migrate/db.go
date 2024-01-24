package main

import (
	"context"
	"database/sql"
	"github.com/uptrace/bun"
	"github.com/uptrace/bun/dialect/pgdialect"
	"github.com/uptrace/bun/driver/pgdriver"
	"github.com/uptrace/bun/extra/bundebug"

	pb "github.com/thesammy2010/api.thesammy2010.com/proto/v1/squash"

	"os"
)

func main() {
	ctx := context.Background()
	pgdb := sql.OpenDB(pgdriver.NewConnector(pgdriver.WithDSN(os.Getenv("DATABASE_URL"))))
	db := bun.NewDB(pgdb, pgdialect.New())
	pgdb.SetMaxOpenConns(1)
	db.AddQueryHook(bundebug.NewQueryHook(
		bundebug.WithVerbose(true),
		bundebug.FromEnv("BUNDEBUG"),
	))

	// Reset Create Squash Player model
	err := db.ResetModel(ctx, &pb.SquashPlayer{})
	if err != nil {
		panic(err)
	}
}
