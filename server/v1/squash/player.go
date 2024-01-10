package squash

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/google/uuid"
	pb "github.com/thesammy2010/api.thesammy2010.com/proto/v1/squash"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// PlayerServer SquashPlayer server type
type PlayerServer struct {
	pb.UnimplementedSquashPlayerServiceServer
}

// NewSquashPlayerServer Function to create new server
func NewSquashPlayerServer() *PlayerServer {
	return &PlayerServer{}
}

// CreateSquashPlayer Function to handle incoming request for creating new squash player
func (s *PlayerServer) CreateSquashPlayer(ctx context.Context, in *pb.CreateSquashPlayerRequest) (*pb.CreateSquashPlayerResponse, error) {
	data, err := json.Marshal(&in)
	fmt.Printf("%s\n", string(data))
	if err != nil {
		return nil, err
	}
	if in.Name == "" {
		return nil, status.Error(codes.FailedPrecondition, "Player `name` is required")
	}
	return &pb.CreateSquashPlayerResponse{Id: uuid.New().String()}, err
}
