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
Good Create Squash Player request
```http request
POST /v1/squash/players?pretty
Content-Type: application/json

{"name": "TheSammy2010", "email_address": "foo@example.com"}
```
```json
{
  "id": "a715ea87-92e2-4a11-80cf-7a9f9f2d9302"
}
```
Bad Create Squash Player request

```http request
POST /v1/squash/players?pretty
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
Good Get squash player request
```http request
GET /v1/squash/players/76d34b99-1e10-4693-b2c2-20b129ad4da1
Content-Type: application/json
```
```json
{
  "squashPlayer": {
    "id": "6622224b-a8eb-4093-bc24-4c8a20f49f25",
    "name": "TheSammy2010",
    "email_address": "foo@example.com",
    "profile_picture": "",
    "created_at": "2024-01-25T00:58:28.819889Z",
    "updated_at": "2024-01-25T00:58:28.819889Z"
  }
}
```
Bad Get squash player request
```http request
GET /v1/squash/players/76d34b99-1e10-4693-b2c2-20b129ad4da1
Content-Type: application/json
```
```json
{
    "code": 3,
    "message": "Player `id` type is not valid UUID",
    "details": []
}
```

```http request
PATCH /v1/squash/players/76d34b99-1e10-4693-b2c2-20b129ad4da1 -d '{"name": "TheSammy2011"}'
```

```json
{
  "squashPlayer": {
    "id": "76d34b99-1e10-4693-b2c2-20b129ad4da1",
    "name": "TheSammy2011",
    "email_address": "foo@example.comssss",
    "profile_picture": "",
    "created_at": "2024-02-05T14:34:41Z",
    "updated_at": "2024-02-05T15:34:44Z"
  }
}
```

TODO
- [ ] Authentication 
  - [X] via Google
- [ ] Routes & Methods
    - [X] `/v1/squash/players/signup` 
    - [X] `/v1/squash/players`
      - [X] GET
      - [X] GET (list)
      - [ ] POST (create) //Deprecated in place of `/v1/squash/players/signup`
      - [X] PATCH (update)
      - [X] DELETE
    - [ ] `/v1/squash/games/singles`
      - [ ] GET
      - [ ] GET (list)
      - [ ] POST (create)
      - [ ] PATCH (update)
      - [ ] DELETE
    - [ ] `/v1/squash/games/doubles`
      - [ ] GET
      - [ ] GET (list)
      - [ ] POST (create)
      - [ ] PATCH (update)
      - [ ] DELETE
- [X] Postgres Setup in Code
- [ ] ORM relationships between tables
- [ ] Handle null fields
- [X] Handle timestamps
- [X] Logging
  - [X] Trace Logging
- [ ] Handle non-registered routes
