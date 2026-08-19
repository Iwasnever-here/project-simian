import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.simulation.world.world import World


SIMULATION_TICK_SECONDS = 1.0

simulation_paused = False
simulation_speed = 1.0

world = World(300, 300)


async def simulation_loop():
    
    while True:
        if not simulation_paused:
            await asyncio.to_thread(
                world.update,
            )

        await asyncio.sleep(
            SIMULATION_TICK_SECONDS
            / simulation_speed
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


app = FastAPI(lifespan=lifespan,)


app.add_middleware( GZipMiddleware,minimum_size=500,)

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

@app.get("/temple")
def get_temple():
    return world.get_temple()

@app.get("/events")
def get_events():
    return world.get_events()

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

@app.get("/monkeys/{monkey_id}")
def get_monkey(monkey_id: int):
    monkey = world.get_monkey(monkey_id)

    if monkey is None:
        raise HTTPException(
            status_code=404,
            detail="Monkey not found",
        )

    return monkey.to_dict()

@app.post("/simulation/pause")
def pause_simulation():
    global simulation_paused

    simulation_paused = True

    return {
        "paused": simulation_paused,
        "speed": simulation_speed,
    }


@app.post("/simulation/resume")
def resume_simulation():
    global simulation_paused

    simulation_paused = False

    return {
        "paused": simulation_paused,
        "speed": simulation_speed,
    }


@app.post("/simulation/speed/{speed}")
def set_simulation_speed(speed: float):
    global simulation_speed

    allowed_speeds = {
        0.5,
        1.0,
        2.0,
        4.0,
    }

    if speed not in allowed_speeds:
        raise HTTPException(
            status_code=400,
            detail="Invalid simulation speed",
        )

    simulation_speed = speed

    return {
        "paused": simulation_paused,
        "speed": simulation_speed,
    }

@app.get("/simulation/status")
def get_simulation_status():
    return {
        "paused": simulation_paused,
        "speed": simulation_speed,
    }