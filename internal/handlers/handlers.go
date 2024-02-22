package handlers

import (
	"context"
	"github.com/felixge/httpsnoop"
	"github.com/rs/cors"
	"github.com/thesammy2010/api.thesammy2010.com/internal/auth"
	"github.com/thesammy2010/api.thesammy2010.com/internal/config"
	"github.com/thesammy2010/api.thesammy2010.com/internal/logger"
	"go.uber.org/zap"
	"net/http"
)

// withLogger This wrapper snoops requests and prints out logs
func withLogging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		m := httpsnoop.CaptureMetrics(next, w, r)
		logger.Info("Request",
			zap.String("method", r.Method),
			zap.Int("status", m.Code),
			zap.String("path", r.URL.Path),
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

		payload, err := auth.ValidateToken(ctx, cfg, *token)
		if err != nil {
			if err.InternalError {
				http.Error(w, err.AsJson(), http.StatusInternalServerError)
			} else {
				http.Error(w, err.AsJson(), http.StatusForbidden)
			}
			return
		}

		//if r.RequestURI = "/"
		r.Header.Set("Grpc-Metadata-User-Google-Account-Id", payload["sub"].(string))
		r.Header.Set("Grpc-Metadata-User-Name", payload["name"].(string))
		r.Header.Set("Grpc-Metadata-User-Picture-Url", payload["picture"].(string))
		next.ServeHTTP(w, r)
	}
}

func withCors(cfg config.Config, handler http.Handler) http.Handler {
	AllowedOrigins := []string{"https://squash.thesammy2010.com"}

	if cfg.Environment == "local" {
		AllowedOrigins = append(AllowedOrigins, "http://localhost:3000")
	}

	c := cors.New(cors.Options{
		AllowedOrigins:   AllowedOrigins,
		AllowedMethods:   []string{http.MethodGet, http.MethodPut, http.MethodPatch},
		AllowedHeaders:   []string{"Authorization", "Content-Type", "Accept-Encoding", "Accept"},
		AllowCredentials: true,
	})
	return c.Handler(handler)
}

// HttpHandler exported function to wrap http handlers into one
func HttpHandler(handler http.Handler, config config.Config) http.Handler {
	if config.HandlerEnablePrettier {
		handler = withPrettier(handler)
	}
	if config.HandlerEnableAuth {
		handler = withJwtAuth(config, handler)
	}
	if config.HandlerEnableCors {
		handler = withCors(config, handler)
	}
	if config.HandlerEnableLogging {
		handler = withLogging(handler)
	}
	return handler
}
