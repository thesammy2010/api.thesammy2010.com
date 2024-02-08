package auth

import (
	"context"
	"encoding/json"
	"github.com/thesammy2010/api.thesammy2010.com/internal/config"
	"github.com/thesammy2010/api.thesammy2010.com/internal/logger"
	"go.uber.org/zap"
	"google.golang.org/api/idtoken"
	"strings"
)

type RequestError struct {
	Error         string `json:"error"`
	InternalError bool   `json:"-"`
}

func (r *RequestError) AsJson() string {
	if data, err := json.Marshal(r); err != nil {
		logger.Error("Error creating error message", zap.String("Content", r.Error))
		return ""
	} else {
		return string(data)
	}
}

func GetTokenFromRequest(auth map[string][]string) (*string, *RequestError) {

	header, ok := auth["Authorization"]
	if !ok {
		header, ok = auth["authorization"]
	}
	headerString := strings.Join(header, "")
	parts := strings.Split(headerString, " ")

	// missing header
	if !ok {
		return nil, &RequestError{Error: "Authorization header is missing"}
	}
	// if there were multiple headers somehow
	if len(header) != 1 {
		return nil, &RequestError{Error: "Only submit one Authorization header"}
	}
	// check if token is there
	if len(parts) != 2 {
		return nil, &RequestError{Error: "Authorization token is malformed or missing"}
	}

	return &parts[1], nil
}

func ValidateToken(ctx context.Context, cfg config.Config, token string) (map[string]interface{}, *RequestError) {
	tokenValidator, err := idtoken.NewValidator(ctx)
	if err != nil {
		logger.Warn("Failed to initialised ID token validator", zap.Error(err))
		return nil, &RequestError{"Internal Server Error", true}
	}

	payload, err := tokenValidator.Validate(context.Background(), token, cfg.ClientId)
	if err != nil {
		logger.Warn("Failed to validate ID token", zap.Error(err))
		return nil, &RequestError{err.Error(), false}
	}
	return payload.Claims, nil
}
