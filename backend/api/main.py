from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.simulation.world.world import World


app = FastAPI()

world = World(20, 20)

# CORS configuration goes HERE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Simian Engine API"
    }


@app.get("/world")
def get_world():
    print(world.get_tile(5, 8))
    return world.to_dict()