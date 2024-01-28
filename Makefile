install:
	brew install bufbuild/buf/buf
	go install github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-grpc-gateway@v2.19.0
	go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.32.0
	go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.3.0
	go install github.com/favadi/protoc-go-inject-tag@v1.4.0

generate:
	buf generate
	protoc-go-inject-tag -input="proto/v1/squash/*.pb.go"

build-app:
	go build -o build

run-app:
	go run cmd/server/main.go

test-app:
	go vet ./...
	golint ./...
	staticcheck ./...
	go test -race -vet=off ./...

run-db-migration-locally:
	go run cmd/migrate/db.go
