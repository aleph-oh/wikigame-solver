from fastapi import FastAPI

from database.constants import Base, engine
from .routers import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Wikipedia Game Solver API",
    description="An API which can be queried for solutions to the Wikipedia game",
    version="0.1",
)


app.include_router(router, prefix="/wikidata")
