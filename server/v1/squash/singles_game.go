package squash

import (
	"context"
	"fmt"
	"github.com/thesammy2010/api.thesammy2010.com/internal/logger"
	pb "github.com/thesammy2010/api.thesammy2010.com/proto/v1/squash"
	"github.com/uptrace/bun"
	"go.uber.org/zap"
	"time"
)

type SquashSinglesGame pb.SquashSinglesGame

var _ bun.BeforeAppendModelHook = (*SquashSinglesGame)(nil)
var _ bun.AfterCreateTableHook = (*SquashSinglesGame)(nil)
var _ bun.BeforeCreateTableHook = (*SquashSinglesGame)(nil)

// BeforeAppendModel Used to update the created_at and updated_at fields on query changes
func (g *SquashSinglesGame) BeforeAppendModel(ctx context.Context, query bun.Query) error {
	now := time.Now().Format(time.RFC3339)
	switch query.(type) {
	case *bun.InsertQuery:
		g.CreatedAt = now
		g.UpdatedAt = now
	case *bun.UpdateQuery:
		g.UpdatedAt = now
	}
	return nil
}

// AfterCreateTable this creates an index on the id column
func (g *SquashSinglesGame) AfterCreateTable(ctx context.Context, query *bun.CreateTableQuery) error {
	logger.Debug("Creating index", zap.String("table", "squash_singles_games"))
	for _, field := range []string{"id"} {
		_, err := query.DB().NewCreateIndex().
			Model((*SquashSinglesGame)(nil)).
			Index(fmt.Sprintf("squash_singles_games_%s_idx", field)).
			Column(field).
			Exec(ctx)
		if err != nil {
			return err
		}
	}
	return nil
}

func (g *SquashSinglesGame) BeforeCreateTable(ctx context.Context, query *bun.CreateTableQuery) error {
	query.
		WithForeignKeys().
		ForeignKey(`("player1_id") REFERENCES "squash_players" ("id") ON DELETE CASCADE`).
		ForeignKey(`("player2_id") REFERENCES "squash_players" ("id") ON DELETE CASCADE`).
		ForeignKey(`("winning_player_id") REFERENCES "squash_players" ("id") ON DELETE CASCADE`)
	return nil
}
