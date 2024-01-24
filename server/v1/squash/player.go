package squash

import (
	"context"
	pb "github.com/thesammy2010/api.thesammy2010.com/proto/v1/squash"
	"github.com/uptrace/bun"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// PlayerServer SquashPlayer server type
type PlayerServer struct {
	pb.UnimplementedSquashPlayerServiceServer
	DB *bun.DB
}

// ValidateCreateSquashPlayerRequest Function to validate if request is valid
func ValidateCreateSquashPlayerRequest(in *pb.CreateSquashPlayerRequest) error {
	if in.Name == "" {
		return status.Error(codes.FailedPrecondition, "Player `name` is required")
	}
	return nil
}

// CreateSquashPlayer Function to handle incoming request for creating new squash player
func (s *PlayerServer) CreateSquashPlayer(ctx context.Context, in *pb.CreateSquashPlayerRequest) (*pb.CreateSquashPlayerResponse, error) {
	//data, err := json.Marshal(&in)
	//fmt.Printf("%s\n", string(data))
	//if err != nil {
	//	return nil, err
	//}
	if err := ValidateCreateSquashPlayerRequest(in); err != nil {
		return nil, err
	}
	var response pb.SquashPlayer
	_, err := s.DB.NewInsert().Model(
		&pb.SquashPlayer{Name: in.Name, EmailAddress: in.EmailAddress, ProfilePicture: in.ProfilePicture},
	).Returning("id").Exec(ctx, &response)
	if err != nil {
		return nil, status.Error(codes.Internal, "Failed to register new player")
	}
	return &pb.CreateSquashPlayerResponse{Id: response.Id}, err
}
