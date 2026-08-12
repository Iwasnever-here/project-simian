import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.simulation.world.world import World


SIMULATION_TICK_SECONDS = 1.0

world = World(300, 300)


async def simulation_loop():
    while True:
        world.update()

        await asyncio.sleep(
            SIMULATION_TICK_SECONDS,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    simulation_task = asyncio.create_task(
        simulation_loop()
    )

    try:
        yield
    finally:
        simulation_task.cancel()

        try:
            await simulation_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    lifespan=lifespan,
)


app.add_middleware(
    GZipMiddleware,
    minimum_size=500,
)

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
        "message": "Simian Engine API",
    }


@app.get("/world/meta")
def get_world_meta():
    return world.meta()


@app.get("/world/chunk/{cx}/{cy}")
def get_world_chunk(
    cx: int,
    cy: int,
):
    max_cx = (
        world.width - 1
    ) // world.chunk_size

    max_cy = (
        world.height - 1
    ) // world.chunk_size

    if not (
        0 <= cx <= max_cx
        and 0 <= cy <= max_cy
    ):
        raise HTTPException(
            status_code=404,
            detail="Chunk out of range",
        )

    return world.get_chunk(
        cx,
        cy,
    )


@app.get("/world/thumbnail")
def get_world_thumbnail():
    return world.thumbnail()


@app.post("/monkeys/spawn")
def spawn_monkey():
    monkey = world.spawn_random_monkey()

    if monkey is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Could not find a spawnable "
                "tile - try again"
            ),
        )

    return monkey.to_dict()


@app.get("/monkeys")
def get_monkeys():
    return world.get_monkeys()