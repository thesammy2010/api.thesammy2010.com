package internal

import (
	"github.com/felixge/httpsnoop"
	"go.uber.org/zap"
	"net/http"
)

//var (
//	config, _ = LoadConfig()
//)

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

//// withBasicAuth this handler does basic auth checking
//func withBasicAuth(h http.Handler) http.Handler {
//	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
//		auth_header_slice, ok := r.Header["Authorization"]
//		if !ok {
//			newBody := `{"error": "Request must be authorized using the Authorization HTTP header"}`
//			r.Body = io.NopCloser(strings.NewReader(newBody))
//			r.ContentLength = int64(len(newBody))
//			r.Response.StatusCode = http.StatusBadRequest
//		}
//		auth_header_bytes := strings.Join(auth_header_slice, "")
//		if subtle.ConstantTimeCompare([]byte(config.ApiKey), []byte(auth_header_bytes)) == 0 {
//			newBody := `{"error": "Credentials are invalid"}`
//			r.Body = io.NopCloser(strings.NewReader(newBody))
//			r.ContentLength = int64(len(newBody))
//			r.Response.StatusCode = http.StatusForbidden
//		}
//		h.ServeHTTP(w, r)
//	})
//}

// HttpHandler exported function to wrap http handlers into one
func HttpHandler(handler http.Handler, config Config) http.Handler {
	if config.HandlerEnablePrettier {
		handler = withPrettier(handler)
	}
	//if config.HandlerEnableBasicAuth {
	//	handler = withBasicAuth(handler)
	//}
	if config.HandlerEnableLogging {
		handler = withLogging(handler)
	}
	return handler
}
