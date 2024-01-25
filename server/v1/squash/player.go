package squash

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"github.com/google/uuid"
	pb "github.com/thesammy2010/api.thesammy2010.com/proto/v1/squash"
	"github.com/uptrace/bun"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/timestamppb"
	"net/mail"
	"time"
)

// PlayerServer SquashPlayer server type
type PlayerServer struct {
	pb.UnimplementedSquashPlayerServiceServer
	DB *bun.DB
}

// DatabaseModel An abstraction that allows for storing extra fields not shown in the struct
type DatabaseModel struct {
	pb.SquashPlayer
	bun.BaseModel `bun:"table:squash_players"`
	CreatedAt     time.Time
	UpdatedAt     time.Time
}

// ToSquashPlayer this converts the database model to the proto model. Only used for transforming the timestamp
func (m *DatabaseModel) ToSquashPlayer() *pb.SquashPlayer {
	return &pb.SquashPlayer{
		Id: m.Id, Name: m.Name, EmailAddress: m.EmailAddress, ProfilePicture: m.ProfilePicture,
		CreatedAt: timestamppb.New(m.CreatedAt), UpdatedAt: timestamppb.New(m.UpdatedAt),
	}
}

var _ bun.BeforeAppendModelHook = (*DatabaseModel)(nil)

// BeforeAppendModel Used to update the created_at and updated_at fields on query changes
func (m *DatabaseModel) BeforeAppendModel(ctx context.Context, query bun.Query) error {
	switch query.(type) {
	case *bun.InsertQuery:
		m.CreatedAt = time.Now()
		m.UpdatedAt = time.Now()
	case *bun.UpdateQuery:
		m.UpdatedAt = time.Now()
	}
	return nil
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

// CreateSquashPlayer Function to handle incoming request for creating new squash player
func (s *PlayerServer) CreateSquashPlayer(ctx context.Context, in *pb.CreateSquashPlayerRequest) (*pb.CreateSquashPlayerResponse, error) {
	if err := validateCreateSquashPlayerRequest(in); err != nil {
		return nil, err
	}
	var check DatabaseModel
	var response DatabaseModel
	now := timestamppb.New(time.Now())

	// check if player already exists
	err := s.DB.NewSelect().Model(&DatabaseModel{SquashPlayer: pb.SquashPlayer{Name: in.Name}}).Where("name = ?", in.Name).WhereOr("email_address = ?", in.EmailAddress).Scan(ctx, &check)
	if err == nil {
		if check.Id != "" {
			return nil, status.Error(codes.AlreadyExists, "Player already exists")
		}
	}
	if err != sql.ErrNoRows {
		return nil, status.Error(codes.Internal, "Internal error registering player")
	}

	// create new user
	_, err = s.DB.NewInsert().Model(
		&DatabaseModel{SquashPlayer: pb.SquashPlayer{Name: in.Name, EmailAddress: in.EmailAddress, ProfilePicture: in.ProfilePicture, CreatedAt: now, UpdatedAt: now}},
	).Returning("id").Exec(ctx, &response)
	if err != nil {
		fmt.Println(err)
		return nil, status.Error(codes.Internal, "Failed to register new player")
	}
	return &pb.CreateSquashPlayerResponse{Id: response.Id}, err
}

// GetSquashPlayer Function to fetch squash player from db
func (s *PlayerServer) GetSquashPlayer(ctx context.Context, in *pb.GetSquashPlayerRequest) (*pb.GetSquashPlayerResponse, error) {
	if err := validateGetSquashPlayerRequest(in); err != nil {
		return nil, err
	}
	var response DatabaseModel
	if err := s.DB.NewSelect().Model(&DatabaseModel{SquashPlayer: pb.SquashPlayer{Id: in.Id}}).WherePK().Scan(ctx, &response); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, fmt.Sprintf("Player with ID `%s` does not exist", in.Id))
		}
		return nil, status.Error(codes.Internal, fmt.Sprintf("Failed to find player with ID `%s`", in.Id))
	}
	return &pb.GetSquashPlayerResponse{SquashPlayer: response.ToSquashPlayer()}, nil
}
