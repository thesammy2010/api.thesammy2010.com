import logging
from contextlib import asynccontextmanager

import dotenv
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import root
from src.routers.go_heavier import locations

dotenv.load_dotenv()


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app_: FastAPI):
    logging.info("running migrations...")
    run_migrations()
    yield
    logging.info("Shutting down...")


app = FastAPI(lifespan=lifespan)
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
app.include_router(root.router)
app.include_router(locations.router)
