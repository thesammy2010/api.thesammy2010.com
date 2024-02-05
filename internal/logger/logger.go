package logger

import (
	"go.uber.org/zap"
)

var Logger *zap.Logger

func init() {
	var err error
	cfg := zap.NewProductionConfig()
	cfg.Level = zap.NewAtomicLevelAt(zap.DebugLevel)
	encCfg := cfg.EncoderConfig
	encCfg.StacktraceKey = ""
	Logger, err = cfg.Build()
	if err != nil {
		panic(err)
	}
}

func Info(message string, fields ...zap.Field) {
	Logger.Info(message, fields...)
}

func Debug(message string, fields ...zap.Field) {
	Logger.Debug(message, fields...)
}

func Warn(message string, fields ...zap.Field) {
	Logger.Warn(message, fields...)
}

func Error(message string, fields ...zap.Field) {
	Logger.Error(message, fields...)
}

func Fatal(message string, fields ...zap.Field) {
	Logger.Fatal(message, fields...)
}
