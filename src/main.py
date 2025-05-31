import dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import squash

dotenv.load_dotenv()

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8000",
    "https://api.thesammy2010.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(squash.router)
