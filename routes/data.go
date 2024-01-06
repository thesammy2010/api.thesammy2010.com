package routes

import (
	"io"
	"net/http"
)

// DataHandler http handler to handle requests coming into the "/data" endpoint for now
func DataHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNotImplemented)
	io.WriteString(w, "This endpoint has not yet been developed\n")
}
