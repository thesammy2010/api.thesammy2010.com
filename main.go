package main

import (
	"fmt"
	"github.com/gorilla/mux"
	"github.com/thesammy2010/api.thesammy2010.com/routes"
	"log"
	"net/http"
	"os"
)

// loggingMiddleware Simple function to log requests
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if os.Getenv("LOG_REQUESTS") == "true" {
			log.Printf("%s %s %s\n", r.Method, r.RequestURI, r.UserAgent())
		}
		next.ServeHTTP(w, r)
	})
}

// function to handle creating the router
func createRouter() *mux.Router {
	router := mux.NewRouter()
	router.StrictSlash(true)
	router.Use(loggingMiddleware)
	router.HandleFunc("/health", routes.HealthCheckHandler)
	router.HandleFunc("/data", routes.DataHandler)
	return router
}

// main entrypoint
func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%s", port), createRouter()))
}
