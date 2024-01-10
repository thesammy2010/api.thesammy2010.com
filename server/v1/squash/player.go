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

type SquashPlayerServer struct {
	pb.UnimplementedSquashPlayerServiceServer
}

func NewSquashPlayerServer() *SquashPlayerServer {
	return &SquashPlayerServer{}
}

func (s *SquashPlayerServer) CreateSquashPlayer(ctx context.Context, in *pb.CreateSquashPlayerRequest) (*pb.CreateSquashPlayerResponse, error) {
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
