package internal

import (
	"github.com/spf13/viper"
	"go.uber.org/zap"
)

var (
	logger = zap.Must(zap.NewProduction())
)

// Config struct to hold config options
type Config struct {
	Environment string `mapstructure:"ENVIRONMENT"`
	GrpcPort    string `mapstructure:"GRPC_PORT"`
	GatewayPort string `mapstructure:"PORT"`
	DatabaseURL string `mapstructure:"DATABASE_URL"`
}

// LoadConfig function that loads config opts from files and env vars
func LoadConfig() (config Config, err error) {
	viper.SetDefault("PORT", "5000")
	viper.SetDefault("GRPC_PORT", "8090")
	viper.AddConfigPath(".")
	viper.SetConfigName(".env")
	viper.SetConfigType("env")
	err = viper.ReadInConfig()
	if err != nil {
		logger.Warn("Failed to read config file", zap.String("configFile", viper.ConfigFileUsed()))
	}
	viper.AutomaticEnv()
	err = viper.Unmarshal(&config)
	return
}
