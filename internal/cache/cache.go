package cache

import (
	"fmt"
	"github.com/patrickmn/go-cache"
	"github.com/thesammy2010/api.thesammy2010.com/internal/logger"
	pb "github.com/thesammy2010/api.thesammy2010.com/proto/v1/squash"
	"go.uber.org/zap"
	"google.golang.org/protobuf/proto"
	"time"
)

type ReferencableSquashPlayer interface {
	GetId() string
	GetGoogleAccountId() string
}

type Cache struct {
	players      *cache.Cache
	singlesGames *cache.Cache
}

func NewCache(defaultExpiration, cachePurgeTime int) *Cache {
	players := cache.New(
		time.Duration(defaultExpiration)*time.Minute,
		time.Duration(cachePurgeTime)*time.Minute,
	)
	singlesGames := cache.New(
		time.Duration(defaultExpiration)*time.Minute,
		time.Duration(cachePurgeTime)*time.Minute,
	)
	logger.Debug("Initialise new cache")
	return &Cache{
		players:      players,
		singlesGames: singlesGames,
	}
}

func (c *Cache) GetSquashPlayer(id string, method pb.GetSquashPlayerRequestType, trace string) (*pb.SquashPlayer, bool) {
	key := fmt.Sprintf("%s-%s", method.String(), id)
	data, ok := c.players.Get(key)
	if ok {
		logger.Debug("Resource found in cache",
			zap.String("Resource", "Player"),
			zap.String("ID", id),
			zap.String("method", method.String()),
			zap.String("trace", trace),
		)
		var player pb.SquashPlayer
		err := proto.Unmarshal(data.([]byte), &player)
		if err != nil {
			logger.Error("Failed to read cache for resource",
				zap.String("Resource", "Player"),
				zap.String("ID", id),
				zap.String("method", method.String()),
				zap.String("trace", trace),
				zap.Error(err),
			)
			return nil, false
		}
		return &player, true
	}
	logger.Debug("Resource not in cache",
		zap.String("Resource", "Player"),
		zap.String("ID", id),
		zap.String("method", method.String()),
		zap.String("trace", trace),
	)
	return nil, false
}

func (c *Cache) GetSquashPlayerList(offset string, trace string) (*pb.ListSquashPlayersResponse, bool) {
	data, ok := c.players.Get("list-" + offset)
	if ok {
		logger.Debug("Resource found in cache",
			zap.String("Resource", "PlayerList"),
			zap.String("ID", offset),
			zap.String("trace", trace),
		)
		var playerListResponse pb.ListSquashPlayersResponse
		err := proto.Unmarshal(data.([]byte), &playerListResponse)
		if err != nil {
			logger.Error("Failed to read cache for resource",
				zap.String("Resource", "PlayerList"),
				zap.String("Offset", offset),
				zap.String("trace", trace),
				zap.Error(err),
			)
			return nil, false
		}
		return &playerListResponse, true
	}
	logger.Debug("Player not in cache",
		zap.String("Resource", "PlayerList"),
		zap.String("Offset", offset),
		zap.String("trace", trace),
	)
	return nil, false
}

func (c *Cache) UpdateSquashPlayer(data *pb.SquashPlayer, trace string) {
	serialised, err := proto.Marshal(data)
	logger.Debug("Updating cache", zap.String("Resource", "Player"), zap.String("ID", data.Id))
	if err != nil {
		logger.Error("Error marshalling data to bytes for cache",
			zap.String("Resource", "Player"),
			zap.String("ID", data.Id),
			zap.String("trace", trace),
			zap.Error(err),
		)
		return
	}
	c.players.Set(fmt.Sprintf("%s-%s", pb.GetSquashPlayerRequestType_METHOD_SQUASH_PLAYER_ID.String(), data.Id), serialised, cache.DefaultExpiration)
	c.players.Set(fmt.Sprintf("%s-%s", pb.GetSquashPlayerRequestType_METHOD_GOOGLE_ACCOUNT_ID.String(), data.GoogleAccountId), serialised, cache.DefaultExpiration)
}

func (c *Cache) UpdateSquashPlayerList(offset, trace string, data *pb.ListSquashPlayersResponse) {
	serialised, err := proto.Marshal(data)
	logger.Debug("Updating cache", zap.String("Resource", "PlayerList"), zap.String("Offset", offset))
	if err != nil {
		logger.Error("Error marshalling data to bytes for cache",
			zap.String("Resource", "PlayerList"),
			zap.String("Offset", offset),
			zap.String("trace", trace),
			zap.Error(err),
		)
		return
	}
	c.players.Set("list-"+offset, serialised, cache.DefaultExpiration)
}

func (c *Cache) DeleteSquashPlayer(data ReferencableSquashPlayer, trace string) {
	c.players.Delete(fmt.Sprintf("%s-%s", pb.GetSquashPlayerRequestType_METHOD_SQUASH_PLAYER_ID.String(), data.GetId()))
	c.players.Delete(fmt.Sprintf("%s-%s", pb.GetSquashPlayerRequestType_METHOD_GOOGLE_ACCOUNT_ID.String(), data.GetGoogleAccountId()))
}
