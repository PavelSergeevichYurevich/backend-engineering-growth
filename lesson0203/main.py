from fastapi import FastAPI

from .db import engine
from .logging_config import setup_logging
from .models import Base
from .routes import router

Base.metadata.create_all(bind=engine)
setup_logging()

app = FastAPI()
app.include_router(router)
