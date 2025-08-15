# TheSammy2010 API

Available at: https://api.thesammy2010.com

### Local development requirements
- pyenv

```bash
pyenv install 3.13.3

python -m venv .venv
source .venv/bin/activate
pip install poetry==2.1.3
poetry install
pre-commit install
```


### Runnning the API```
```bash
fastapi dev src/main.py
```

```http request
POST /users
Authorization: Bearer <Google OAuth2 token>
```
```json
{
  "user_id": "<uuid>"
}
```
or
```bash
curl \
  -X POST localhost:8000/users \
  -H "Authorization: Bearer $TOKEN"
```

### Connecting to the database
```bash
fly postgres connect -a thesammy2010
```

or
```bash
fly ssh console -a api-thesammy2010-com
echo $DATABASE_URL
fly proxy 15432:5432 -a thesammy2010
```
