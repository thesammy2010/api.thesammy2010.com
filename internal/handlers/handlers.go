package handlers

import (
	"context"
	"github.com/felixge/httpsnoop"
	"github.com/thesammy2010/api.thesammy2010.com/internal/auth"
	"github.com/thesammy2010/api.thesammy2010.com/internal/config"
	"github.com/thesammy2010/api.thesammy2010.com/internal/logger"
	"go.uber.org/zap"
	"net/http"
)

// withLogger This wrapper snoops requests and prints out logs
func withLogging(handler http.Handler) http.Handler {
	return http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		m := httpsnoop.CaptureMetrics(handler, writer, request)
		logger.Info("Request",
			zap.String("method", request.Method),
			zap.Int("status", m.Code),
			zap.String("path", request.URL.Path),
		)
	})
}

// withPrettier helper function to allow pretty to be a path URL
func withPrettier(h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if _, ok := r.URL.Query()["pretty"]; ok {
			r.Header.Set("Accept", "application/json+pretty")
		}
		h.ServeHTTP(w, r)
	})
}

func withJwtAuth(cfg config.Config, next http.Handler) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {

		ctx := context.Background()

		token, err := auth.GetTokenFromRequest(r.Header)
		if err != nil {
			http.Error(w, err.AsJson(), http.StatusForbidden)
			return
		}

		user, err := auth.ValidateToken(ctx, cfg, *token)
		if err != nil {
			if err.InternalError {
				http.Error(w, err.AsJson(), http.StatusInternalServerError)
			} else {
				http.Error(w, err.AsJson(), http.StatusForbidden)
			}
			return
		}

		w.Header().Set("X-Google-User-Id", user.UserId)

		next.ServeHTTP(w, r)
	}
}

// HttpHandler exported function to wrap http handlers into one
func HttpHandler(handler http.Handler, config config.Config) http.Handler {
	if config.HandlerEnablePrettier {
		handler = withPrettier(handler)
	}
	if config.HandlerEnableAuth {
		handler = withJwtAuth(config, handler)
	}
	if config.HandlerEnableLogging {
		handler = withLogging(handler)
	}
	return handler
}
