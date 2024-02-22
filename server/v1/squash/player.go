package squash

import (
	"context"
	"database/sql"
	"errors"
	"github.com/golang/protobuf/ptypes/empty"
	"github.com/google/uuid"
	"github.com/thesammy2010/api.thesammy2010.com/internal/logger"
	pb "github.com/thesammy2010/api.thesammy2010.com/proto/v1/squash"
	"github.com/uptrace/bun"
	"go.uber.org/zap"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
	"strings"
	"time"
)

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
	if err == nil {
		_, err = query.DB().NewCreateIndex().
			Model((*SquashPlayer)(nil)).
			Index("squash_player_google_account_id_idx").
			Column("google_account_id").
			Exec(ctx)
	}
	return err
}

// validateRequestById function to validate incoming requests to GET /v1/squash/players/:id
func validateRequestById(in RequestById, trace string) error {
	if in.GetId() == "" {
		return status.Error(codes.InvalidArgument, "Player `id` is required")
	}
	if _, err := uuid.Parse(in.GetId()); err != nil {
		logger.Debug("Field is not valid UUID",
			zap.String("Resource", "Player"),
			zap.String("ID", in.GetId()),
			zap.String("trace", trace),
			zap.Error(err),
		)
		return status.Error(codes.InvalidArgument, "Player `id` type is not valid UUID")
	}
	return nil
}

func validateGetSquashPlayersRequest(in *pb.ListSquashPlayersRequest, trace string) error {
	if in.Offset == "" {
		return nil
	}
	if _, err := uuid.Parse(in.Offset); err != nil {
		logger.Debug("Field is not valid UUID",
			zap.String("Resource", "ListPlayer"),
			zap.String("Offset", in.Offset),
			zap.String("trace", trace),
			zap.Error(err),
		)
		return status.Error(codes.InvalidArgument, "Offset type is not valid UUID")
	}
	return nil
}

func validateUpdateSquashPlayerRequest(in *pb.UpdateSquashPlayerRequest, trace string) error {
	if in.Id == "" {
		return status.Error(codes.InvalidArgument, "Player `id` is required")
	}
	if in.Name != nil {
		if in.Name.GetValue() == "" {
			return status.Error(codes.InvalidArgument, "If `name` is provided, it must not be empty")
		}
	}
	if in.ProfilePicture != nil {
		if in.ProfilePicture.GetValue() == "" {
			return status.Error(codes.InvalidArgument, "If `profile_picture` is provided, it must not be empty")
		}
	}
	return nil
}

func validateGetSquashPlayerRequest(in *pb.GetSquashPlayerRequest, trace string) error {
	switch in.Method {
	case pb.GetSquashPlayerRequestType_METHOD_UNSET:
		return status.Error(codes.InvalidArgument, "Value for `method` is not valid")
	case pb.GetSquashPlayerRequestType_METHOD_SQUASH_PLAYER_ID:
		return validateRequestById(in, trace)
	case pb.GetSquashPlayerRequestType_METHOD_GOOGLE_ACCOUNT_ID:
		if in.Id == "" {
			return status.Error(codes.InvalidArgument, "Player `id` is required")
		}
	}
	return nil
}

// GetSquashPlayer Function to fetch squash player from db
func (s *PlayerServer) GetSquashPlayer(ctx context.Context, in *pb.GetSquashPlayerRequest) (*pb.GetSquashPlayerResponse, error) {
	trace := uuid.New().String()

	// validate request
	if err := validateGetSquashPlayerRequest(in, trace); err != nil {
		return nil, err
	}

	// check cache
	if player, ok := s.Cache.GetSquashPlayer(in.Id, in.Method, trace); ok {
		return &pb.GetSquashPlayerResponse{SquashPlayer: player}, nil
	}

	// construct query
	query := s.DB.NewSelect()
	switch in.Method {
	case pb.GetSquashPlayerRequestType_METHOD_SQUASH_PLAYER_ID:
		query = query.Model(&SquashPlayer{Id: in.Id}).WherePK()
	case pb.GetSquashPlayerRequestType_METHOD_GOOGLE_ACCOUNT_ID:
		query = query.Model(&SquashPlayer{}).Where("google_account_id = ?", in.Id)
	}

	// execute query
	var response pb.SquashPlayer
	if err := query.Scan(ctx, &response); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, "Player does not exist")
		}
		logger.Error("Unknown error fetching resource from db",
			zap.String("Resource", "Player"),
			zap.String("ID", in.Id),
			zap.String("trace", trace),
			zap.Error(err),
		)
		return nil, status.Error(codes.Internal, "Failed to find player")
	}

	// update cache
	s.Cache.UpdateSquashPlayer(&response, trace)

	return &pb.GetSquashPlayerResponse{SquashPlayer: &response}, nil
}

// ListSquashPlayers Function to list squash players, pagination based on ID
func (s *PlayerServer) ListSquashPlayers(ctx context.Context, in *pb.ListSquashPlayersRequest) (*pb.ListSquashPlayersResponse, error) {
	trace := uuid.New().String()

	// validate request
	if err := validateGetSquashPlayersRequest(in, trace); err != nil {
		return nil, err
	}

	// check cache
	if players, ok := s.Cache.GetSquashPlayerList(in.Offset, trace); ok {
		return players, nil
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
		logger.Error("Unknown error fetching player from db",
			zap.String("Resource", "PlayerList"),
			zap.String("Offset", in.Offset),
			zap.String("trace", trace),
			zap.Error(err),
		)
		return nil, status.Error(codes.Internal, "Failed to find players")
	}
	apiResponse := &pb.ListSquashPlayersResponse{SquashPlayers: response}

	// update cache
	s.Cache.UpdateSquashPlayerList(in.Offset, trace, apiResponse)

	return apiResponse, nil
}

func (s *PlayerServer) UpdateSquashPlayer(ctx context.Context, in *pb.UpdateSquashPlayerRequest) (*pb.UpdateSquashPlayerResponse, error) {
	trace := uuid.New().String()
	var response pb.SquashPlayer

	// validate request
	if err := validateUpdateSquashPlayerRequest(in, trace); err != nil {
		return nil, err
	}

	// check cache if user exists in cache or check db
	_, ok := s.Cache.GetSquashPlayer(in.Id, pb.GetSquashPlayerRequestType_METHOD_SQUASH_PLAYER_ID, trace)
	if !ok {
		_, err := s.GetSquashPlayer(ctx, &pb.GetSquashPlayerRequest{Id: in.Id})
		if err != nil {
			logger.Error("Error checking if user already exists",
				zap.String("Resource", "Player"),
				zap.String("ID", in.Id),
				zap.String("trace", trace),
				zap.Error(err),
			)
			return nil, err
		}
	}

	// update in db
	dbRes, err := s.DB.NewUpdate().
		Model(&SquashPlayer{Id: in.Id, ProfilePicture: in.ProfilePicture.GetValue(), Name: in.Name.GetValue()}).
		OmitZero().
		WherePK().
		Returning("*").
		Exec(ctx, &response)
	if err != nil {
		logger.Error("Error Running update in db",
			zap.String("Resource", "Player"),
			zap.String("ID", in.Id),
			zap.String("trace", trace),
			zap.Error(err),
		)
		return nil, status.Error(codes.Internal, "Error occurred updating resource")
	}
	rows, err := dbRes.RowsAffected()
	if rows == 0 {
		logger.Warn("No rows effected from UPDATE statement",
			zap.String("Resource", "Player"),
			zap.String("ID", in.Id),
			zap.String("trace", trace),
		)
		return nil, status.Error(codes.NotFound, "Player does not exist")
	}
	if err != nil {
		logger.Error("Error occurred when updating record",
			zap.String("Resource", "Player"),
			zap.String("ID", in.Id),
			zap.String("trace", trace),
			zap.Error(err),
		)
		return nil, status.Error(codes.Internal, "Internal error updating Player")
	}
	logger.Debug("Resource successfully updated",
		zap.String("Resource", "Player"),
		zap.String("ID", in.Id),
		zap.String("trace", trace),
	)

	// update cache
	s.Cache.UpdateSquashPlayer(&response, trace)

	return &pb.UpdateSquashPlayerResponse{SquashPlayer: &response}, nil
}

func (s *PlayerServer) DeleteSquashPlayer(ctx context.Context, in *pb.DeleteSquashPlayerRequest) (*pb.DeleteSquashPlayerResponse, error) {
	trace := uuid.New().String()

	// validate request
	if err := validateRequestById(in, trace); err != nil {
		return nil, err
	}

	// check cache
	check, err := s.GetSquashPlayer(ctx, &pb.GetSquashPlayerRequest{Id: in.Id, Method: pb.GetSquashPlayerRequestType_METHOD_SQUASH_PLAYER_ID})
	if err != nil {
		return nil, err
	}

	// delete from db
	dbRes, err := s.DB.NewDelete().Model(&SquashPlayer{Id: in.Id}).WherePK().Returning("NULL").Exec(ctx)
	if err != nil {
		logger.Error("Error Running update in db",
			zap.String("Resource", "Player"),
			zap.String("ID", in.Id),
			zap.String("trace", trace),
			zap.Error(err),
		)
		return nil, status.Error(codes.Internal, "Error occurred updating resource")
	}
	rows, err := dbRes.RowsAffected()
	if rows == 0 {
		logger.Warn("No rows effected from DELETE statement",
			zap.String("Resource", "Player"),
			zap.String("ID", in.Id),
			zap.String("trace", trace),
		)
		return nil, status.Error(codes.NotFound, "Player does not exist")
	}
	if err != nil {
		logger.Error("Error occurred when deleting record",
			zap.String("Resource", "Player"),
			zap.String("ID", in.Id),
			zap.String("trace", trace),
			zap.Error(err),
		)
		return nil, status.Error(codes.Internal, "Internal error deleting Player")
	}
	logger.Debug("Resource successfully deleted",
		zap.String("Resource", "Player"),
		zap.String("ID", in.Id),
		zap.String("trace", trace),
	)

	// delete from cache
	s.Cache.DeleteSquashPlayer(check.SquashPlayer, trace)

	return &pb.DeleteSquashPlayerResponse{}, nil
}

func (s *PlayerServer) Login(ctx context.Context, in *empty.Empty) (*pb.CreateSquashPlayerResponse, error) {

	trace := uuid.New().String()
	var response pb.SquashPlayer

	// get header from ctx
	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		logger.Warn("Failed to read request context", zap.String("trace", trace))
		return nil, status.Error(codes.Internal, "Internal Error")
	}

	// get attributes from token
	rawPlayer := &SquashPlayer{
		GoogleAccountId: strings.Join(md.Get("User-Google-Account-Id"), ""),
		Name:            strings.Join(md.Get("User-Name"), ""),
		ProfilePicture:  strings.Join(md.Get("User-Picture-Url"), ""),
	}

	// check if player already exists
	check, err := s.GetSquashPlayer(ctx, &pb.GetSquashPlayerRequest{Id: rawPlayer.GoogleAccountId, Method: pb.GetSquashPlayerRequestType_METHOD_GOOGLE_ACCOUNT_ID})
	if err == nil {
		return &pb.CreateSquashPlayerResponse{
			Id: check.SquashPlayer.Id,
		}, nil
	}
	if !strings.HasPrefix(err.Error(), "rpc error: code = NotFound") {
		logger.Error("Unknown error creating resource",
			zap.String("Resource", "Player"),
			zap.String("ID", rawPlayer.GoogleAccountId),
			zap.String("trace", trace),
			zap.Error(err),
		)
		return nil, status.Error(codes.Internal, "Failed to register new player")
	}

	// create user
	_, err = s.DB.NewInsert().Model(rawPlayer).Returning("*").Exec(ctx, &response)
	if err != nil {
		logger.Error("Unknown error creating resource",
			zap.String("Resource", "Player"),
			zap.String("ID", rawPlayer.GoogleAccountId),
			zap.String("trace", trace),
			zap.Error(err),
		)
		return nil, status.Error(codes.Internal, "Failed to register new player")
	}
	// update cache
	s.Cache.UpdateSquashPlayer(&response, trace)

	// return user
	return &pb.CreateSquashPlayerResponse{Id: response.Id}, nil
}
