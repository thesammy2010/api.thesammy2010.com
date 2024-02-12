package squash

import (
	"github.com/thesammy2010/api.thesammy2010.com/internal/cache"
	"github.com/thesammy2010/api.thesammy2010.com/internal/config"
	pb "github.com/thesammy2010/api.thesammy2010.com/proto/v1/squash"
	"github.com/uptrace/bun"
)

// PlayerServer SquashPlayer server type
type PlayerServer struct {
	pb.UnimplementedSquashPlayerServiceServer
	DB     *bun.DB
	Cache  *cache.Cache
	Config *config.Config
}

type RequestById interface {
	GetId() string
}
