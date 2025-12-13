import dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import root
from src.routers.go_heavier import config, exercises, locations

dotenv.load_dotenv()


app = FastAPI(title="TheSammy2010 API", version="1.0.0")
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "https://api.thesammy2010.com",
    "https://thesammy2010.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(root.router)
app.include_router(locations.router)
app.include_router(exercises.router)
app.include_router(config.router)
