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
	ApiKey      string `mapstructure:"API_KEY"`
	// http handler flags
	HandlerEnableLogging   bool `mapstructure:"HANDLERS_ENABLE_LOGGING"`
	HandlerEnablePrettier  bool `mapstructure:"HANDLERS_ENABLE_PRETTIER"`
	HandlerEnableBasicAuth bool `mapstructure:"HANDLERS_ENABLE_BASIC_AUTH"`
}

// LoadConfig function that loads config opts from files and env vars
func LoadConfig() (config Config, err error) {
	viper.SetDefault("PORT", "5000")
	viper.SetDefault("GRPC_PORT", "8090")
	viper.SetDefault("API_KEY", "")
	viper.SetDefault("HANDLERS_ENABLE_LOGGING", true)
	viper.SetDefault("HANDLERS_ENABLE_PRETTIER", false)
	viper.SetDefault("HANDLERS_ENABLE_BASIC_AUTH", false)
	viper.AddConfigPath(".")
	viper.SetConfigName(".env")
	viper.SetConfigType("env")

	err = viper.BindEnv("DATABASE_URL", "DATABASE_URL")
	if err != nil {
		logger.Warn("Failed to bind environment variable `DATABASE_URL`")
		return
	}

	err = viper.ReadInConfig()
	if err != nil {
		logger.Warn("Failed to read config file", zap.String("configFile", viper.ConfigFileUsed()))
	}
	viper.AutomaticEnv()
	err = viper.Unmarshal(&config)
	logger.Info("Running with config",
		zap.String("Environment", config.Environment),
		zap.String("GrpcPort", config.GrpcPort),
		zap.String("GatewayPort", config.GatewayPort),
		zap.Bool("HandlerEnableLogging", config.HandlerEnableLogging),
		zap.Bool("HandlerEnablePrettier", config.HandlerEnablePrettier),
		zap.Bool("HandlerEnableBasicAuth", config.HandlerEnableBasicAuth),
	)
	return
}
