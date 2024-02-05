package cache

import (
	"github.com/patrickmn/go-cache"
	"github.com/thesammy2010/api.thesammy2010.com/internal/logger"
	pb "github.com/thesammy2010/api.thesammy2010.com/proto/v1/squash"
	"go.uber.org/zap"
	"google.golang.org/protobuf/proto"
	"time"
)

type Cache struct {
	players *cache.Cache
}

func NewCache(defaultExpiration, cachePurgeTime int) *Cache {
	c := cache.New(
		time.Duration(defaultExpiration)*time.Minute,
		time.Duration(cachePurgeTime)*time.Minute,
	)
	logger.Debug("Initialise new cache")
	return &Cache{
		players: c,
	}
}

func (c *Cache) GetSquashPlayer(id string) (*pb.SquashPlayer, bool) {
	data, ok := c.players.Get(id)
	if ok {
		logger.Debug("Resource found in cache", zap.String("Resource", "Player"), zap.String("ID", id))
		var player pb.SquashPlayer
		err := proto.Unmarshal(data.([]byte), &player)
		if err != nil {
			logger.Error("Failed to read cache for resource", zap.String("Resource", "Player"), zap.String("ID", id), zap.Error(err))
			return nil, false
		}
		return &player, true
	}
	logger.Debug("Player not in cache", zap.String("ID", id))
	return nil, false
}

func (c *Cache) UpdateSquashPlayer(data *pb.SquashPlayer) bool {
	serialised, err := proto.Marshal(data)
	logger.Debug("Updating cache", zap.String("Resource", "Player"), zap.String("ID", data.Id))
	if err != nil {
		logger.Error("Error marshalling data to bytes for cache", zap.String("Resource", "Player"), zap.String("ID", data.Id))
		return false
	}
	c.players.Set(data.Id, serialised, cache.DefaultExpiration)
	return true
}
