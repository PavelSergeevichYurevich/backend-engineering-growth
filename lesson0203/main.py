from fastapi import FastAPI

from .db import engine
from .models import Base
from .routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(router)
