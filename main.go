package main

import (
	"context"
	"database/sql"
	"flag"
	"fmt"
	"github.com/felixge/httpsnoop"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	pb "github.com/thesammy2010/api.thesammy2010.com/proto/v1/squash"
	"github.com/thesammy2010/api.thesammy2010.com/server/v1/squash"
	"github.com/uptrace/bun"
	"github.com/uptrace/bun/dialect/pgdialect"
	"github.com/uptrace/bun/driver/pgdriver"
	"github.com/uptrace/bun/extra/bundebug"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/encoding/protojson"
	"log"
	"net"
	"net/http"
	"os"
)

var (
	grpcPort = flag.String("gprc_port", "8090", "Port name for the gRPC service")
)

func withLogger(handler http.Handler) http.Handler {
	return http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		m := httpsnoop.CaptureMetrics(handler, writer, request)
		log.Printf("http[%d] -- %s\n", m.Code, request.URL.Path)
	})
}

func main() {

	flag.Parse()
	port := os.Getenv("PORT")
	if port == "" {
		port = "5000"
	}

	// connect to Postgres
	pgdb := sql.OpenDB(pgdriver.NewConnector(pgdriver.WithDSN(os.Getenv("DATABASE_URL"))))
	db := bun.NewDB(pgdb, pgdialect.New())
	pgdb.SetMaxOpenConns(1)
	db.AddQueryHook(bundebug.NewQueryHook(
		//bundebug.WithVerbose(true),
		bundebug.FromEnv("BUNDEBUG"),
	))

	// Reserve port
	lis, err := net.Listen("tcp", ":"+*grpcPort)
	if err != nil {
		log.Fatalln("Failed to listen:", err)
	}

	// start gRPC squashPlayerServer
	s := grpc.NewServer()
	// Register SquashPlayer endpoint
	pb.RegisterSquashPlayerServiceServer(s, &squash.PlayerServer{DB: db})
	log.Printf("Serving gRPC on 0.0.0.0:%s\n", *grpcPort)
	go func() {
		log.Fatalln(s.Serve(lis))
	}()

	// Create a client connection to the gRPC squashPlayerServer
	conn, err := grpc.DialContext(
		context.Background(),
		fmt.Sprintf("0.0.0.0:%s", *grpcPort),
		grpc.WithBlock(),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		log.Fatalln("Failed to dial squashPlayerServer:", err)
	}

	gwmux := runtime.NewServeMux(
		runtime.WithMarshalerOption("application/json+pretty", &runtime.JSONPb{
			MarshalOptions: protojson.MarshalOptions{
				Indent:    "  ",
				Multiline: true,
			},
			UnmarshalOptions: protojson.UnmarshalOptions{
				DiscardUnknown: true,
			},
		}),
	)
	prettier := func(h http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if _, ok := r.URL.Query()["pretty"]; ok {
				r.Header.Set("Accept", "application/json+pretty")
			}
			h.ServeHTTP(w, r)
		})
	}
	// Register Squash Player proxy
	err = pb.RegisterSquashPlayerServiceHandler(context.Background(), gwmux, conn)
	if err != nil {
		log.Fatalln("Failed to register gateway:", err)
	}

	gwServer := &http.Server{
		Addr:    ":" + port,
		Handler: withLogger(prettier(gwmux)),
	}
	log.Printf("Serving gRPC-Gateway on http://0.0.0.0:%s\n", port)
	log.Fatalln(gwServer.ListenAndServe())
}
