package squash

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"github.com/google/uuid"
	"github.com/thesammy2010/api.thesammy2010.com/internal/cache"
	"github.com/thesammy2010/api.thesammy2010.com/internal/logger"
	pb "github.com/thesammy2010/api.thesammy2010.com/proto/v1/squash"
	"github.com/uptrace/bun"
	"go.uber.org/zap"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"net/mail"
	"time"
)

// PlayerServer SquashPlayer server type
type PlayerServer struct {
	pb.UnimplementedSquashPlayerServiceServer
	DB    *bun.DB
	Cache *cache.Cache
}

// SquashPlayer only used for the auto update of the original model
type SquashPlayer pb.SquashPlayer // nolint:staticcheck

var _ bun.BeforeAppendModelHook = (*SquashPlayer)(nil)
var _ bun.AfterCreateTableHook = (*SquashPlayer)(nil)

// BeforeAppendModel Used to update the created_at and updated_at fields on query changes
func (p *SquashPlayer) BeforeAppendModel(ctx context.Context, query bun.Query) error {
	now := time.Now().Format(time.RFC3339)
	switch query.(type) {
	case *bun.InsertQuery:
		p.CreatedAt = now
		p.UpdatedAt = now
	case *bun.UpdateQuery:
		p.UpdatedAt = now
	}
	return nil
}

// AfterCreateTable this creates an index on the id column
func (p *SquashPlayer) AfterCreateTable(ctx context.Context, query *bun.CreateTableQuery) error {
	logger.Debug("Creating index", zap.String("table", "squash_players"))
	_, err := query.DB().NewCreateIndex().
		Model((*SquashPlayer)(nil)).
		Index("squash_player_id_idx").
		Column("id").
		Exec(ctx)
	return err
}

// validateCreateSquashPlayerRequest Function to validate if request is valid
func validateCreateSquashPlayerRequest(in *pb.CreateSquashPlayerRequest) error {
	// check name
	if in.Name == "" {
		return status.Error(codes.InvalidArgument, "Player `name` is required")
	}
	// check email address
	if in.EmailAddress == "" {
		return status.Error(codes.InvalidArgument, "Player `email_address` is required")
	}
	if _, err := mail.ParseAddress(in.EmailAddress); err != nil {
		return status.Error(codes.InvalidArgument, "Player `email_address` is not valid RFC 5322 email address")
	}
	return nil
}

// validateGetSquashPlayerRequest function to validate incoming requests to GET /v1/squash/players/:id
func validateGetSquashPlayerRequest(in *pb.GetSquashPlayerRequest) error {
	if in.Id == "" {
		return status.Error(codes.InvalidArgument, "Player `id` is required")
	}
	if _, err := uuid.Parse(in.Id); err != nil {
		return status.Error(codes.InvalidArgument, "Player `id` type is not valid UUID")
	}
	return nil
}

func validateGetSquashPlayersRequest(in *pb.ListSquashPlayersRequest) error {
	if in.Offset == "" {
		return nil
	}
	if _, err := uuid.Parse(in.Offset); err != nil {
		return status.Error(codes.InvalidArgument, "Offset type is not valid UUID")
	}
	return nil
}

// CreateSquashPlayer Function to handle incoming request for creating new squash player
func (s *PlayerServer) CreateSquashPlayer(ctx context.Context, in *pb.CreateSquashPlayerRequest) (*pb.CreateSquashPlayerResponse, error) {
	if err := validateCreateSquashPlayerRequest(in); err != nil {
		return nil, err
	}
	var check pb.SquashPlayer
	var response pb.SquashPlayer

	// check if player already exists
	err := s.DB.NewSelect().Model(&SquashPlayer{Name: in.Name}).Where("email_address = ?", in.EmailAddress).Scan(ctx, &check)
	if err == nil {
		if check.Id != "" {
			return nil, status.Error(codes.AlreadyExists, "Player already exists")
		}
	}
	if !errors.Is(err, sql.ErrNoRows) {
		return nil, status.Error(codes.Internal, "Internal error registering player")
	}

	// create new user
	_, err = s.DB.NewInsert().Model(
		&SquashPlayer{Name: in.Name, EmailAddress: in.EmailAddress, ProfilePicture: in.ProfilePicture},
	).Returning("*").Exec(ctx, &response)
	if err != nil {
		logger.Error("Unknown error inserting player into db",
			zap.String("email", in.EmailAddress),
		)
		return nil, status.Error(codes.Internal, "Failed to register new player")
	}

	// update cache
	s.Cache.UpdateSquashPlayer(&response)

	return &pb.CreateSquashPlayerResponse{Id: response.Id}, err
}

// GetSquashPlayer Function to fetch squash player from db
func (s *PlayerServer) GetSquashPlayer(ctx context.Context, in *pb.GetSquashPlayerRequest) (*pb.GetSquashPlayerResponse, error) {
	if err := validateGetSquashPlayerRequest(in); err != nil {
		return nil, err
	}

	// check cache
	if player, ok := s.Cache.GetSquashPlayer(in.Id); ok {
		return &pb.GetSquashPlayerResponse{SquashPlayer: player}, nil
	}

	var response pb.SquashPlayer
	if err := s.DB.NewSelect().Model(&SquashPlayer{Id: in.Id}).WherePK().Scan(ctx, &response); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, fmt.Sprintf("Player with ID `%s` does not exist", in.Id))
		}
		logger.Error("Unknown error fetching player from db",
			zap.String("squash_player", in.Id),
		)
		return nil, status.Error(codes.Internal, fmt.Sprintf("Failed to find player with ID `%s`", in.Id))
	}

	// update cache
	s.Cache.UpdateSquashPlayer(&response)

	return &pb.GetSquashPlayerResponse{SquashPlayer: &response}, nil
}

// ListSquashPlayers Function to list squash players, pagination based on ID
func (s *PlayerServer) ListSquashPlayers(ctx context.Context, in *pb.ListSquashPlayersRequest) (*pb.ListSquashPlayersResponse, error) {
	if err := validateGetSquashPlayersRequest(in); err != nil {
		return nil, err
	}
	var response []*pb.SquashPlayer
	query := s.DB.NewSelect().Model(&SquashPlayer{}).Order("id ASC").Limit(10)
	if in.Offset != "" {
		query.Where("id > ?", in.Offset)
	}
	if err := query.Scan(ctx, &response); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, "There are no players in the database")
		}
		logger.Error("Unknown error fetching player from db")
		return nil, status.Error(codes.Internal, "Failed to find players")
	}
	return &pb.ListSquashPlayersResponse{SquashPlayers: response}, nil
}
