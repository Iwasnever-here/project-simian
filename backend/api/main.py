from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.simulation.world.world import World


app = FastAPI()

# Compresses repetitive chunk/terrain JSON well - cheap win, no client changes needed
app.add_middleware(GZipMiddleware, minimum_size=500)

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


world = World(300, 300)


@app.get("/")
def root():
    return {
        "message": "Simian Engine API"
    }


@app.get("/world/meta")
def get_world_meta():
    # Frontend fetches this once on load - no tile data, just dimensions
    return world.meta()


@app.get("/world/chunk/{cx}/{cy}")
def get_world_chunk(cx: int, cy: int):
    max_cx = (world.width - 1) // world.chunk_size
    max_cy = (world.height - 1) // world.chunk_size

    if not (0 <= cx <= max_cx and 0 <= cy <= max_cy):
        raise HTTPException(status_code=404, detail="Chunk out of range")

    return world.get_chunk(cx, cy)


@app.get("/world/thumbnail")
def get_world_thumbnail():
    # Small pre-downsampled terrain map for the minimap - fetched once
    return world.thumbnail()