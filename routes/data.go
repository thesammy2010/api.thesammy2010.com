package routes

import (
	"io"
	"net/http"
)

// TODO implement something here
// data Structure for holding some data
type data struct {
	id     string `json:"id"`
	colour string ``
}

// DataHandler http handler to handle requests coming into the "/data" endpoint for now
func DataHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNotImplemented)

	io.WriteString(w, "This endpoint has not yet been developed\n")

}
