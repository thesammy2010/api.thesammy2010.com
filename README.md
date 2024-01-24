# api.thesammy2010.com
> gRPC HTTP repo for https://api.thesammy2010.com

### Setup
```bash
make install
```

### Running Locally
```bash
make run-app
```
### Usage
```http request
POST http://localhost:5000/v1/squash/players?pretty
Content-Type: application/json

{"name": "TheSammy2010"}
```
```json
{
  "id": "a715ea87-92e2-4a11-80cf-7a9f9f2d9302"
}
```
```http request
POST http://localhost:5000/v1/squash/players?pretty
Content-Type: application/json

{"name": ""}
```
```json
{
    "code": 9, 
    "message": "Player `name` is required", 
    "details": []
}
```

TODO
- [ ] Authentication
- [ ] Other routes
- [ ] Other methods
- [x] Postgres Setup in Code
- [ ] ORM relationships between tables
- [ ] Handle null fields
- [ ] Logging
