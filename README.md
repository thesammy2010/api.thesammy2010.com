# api.thesammy2010.com
> gRPC HTTP repo for https://api.thesammy2010.com

### Setup
```bash
brew install bufbuild/buf/buf
go install github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-grpc-gateway@latest 
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest 
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
buf generate
go run server/main.go
```
### Usage

```http request
POST localhost:5000/v1/squash/players?pretty -d '{"name": "TheSammy2010"}'
Content-Type: application/json

{
  "id": "a715ea87-92e2-4a11-80cf-7a9f9f2d9302"
}
```

TODO
- Authentication
- Other routes
- Postgres setup
