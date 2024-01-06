package routes

import (
	"fmt"
	"io"
	"net/http"
)

// HealthCheckHandler simple function to call back
func HealthCheckHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	// throw error if non-GET received
	if r.Method != http.MethodGet {
		w.WriteHeader(http.StatusMethodNotAllowed)
		io.WriteString(w, fmt.Sprintf(`{"error": "Method '%s' is not supported. Use '%s'"}`, r.Method, http.MethodGet))
		return
	}

	w.WriteHeader(http.StatusOK)
	io.WriteString(w, `{"alive": true}`)
}
