from google.auth.transport import requests
from google.oauth2 import id_token
from pydantic import BaseModel

from src.config import Config


class CommonHeaders(BaseModel):
    authorization: str


def decode_token(token: str):
    return id_token.verify_oauth2_token(
        token, requests.Request(), Config.GOOGLE_CLIENT_ID
    )
