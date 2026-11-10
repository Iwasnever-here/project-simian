import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.simulation.agents.monkey.monkey_learning import get_controlled_q_values
from backend.simulation.world.world import World
from backend.simulation.agents.monkey.monkey_constants import VISION_RANGE


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

@app.get("/tourists")
def tourists_endpoint():
    return world.get_tourists()

@app.get("/tourists/{tourist_id}")
def get_tourist(tourist_id: int):
    with world.lock:
        tourist = world.get_tourist(tourist_id)
        if tourist is None:
            raise HTTPException(
                status_code=404,
                detail="Tourist not found",
            )
        return {
            **tourist.to_dict(),
            "pending_trade_offer": world.get_trade_offer_summary(tourist_id=tourist_id),
        }

@app.get("/boat-landing")
def boat_landing_endpoint():
    return world.get_boat_landing()

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
    with world.lock:
        monkey = world.get_monkey(monkey_id)
        if monkey is None:
            raise HTTPException(
                status_code=404,
                detail="Monkey not found",
            )
        return {
            **monkey.to_dict(),
            "pending_trade_offer": world.get_trade_offer_summary(monkey_id=monkey_id),
        }

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
        1.0,
        8.0,
        32.0,
        64.0,
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
    with world.lock:
        current = world.population_sample()
        history = world.population_history
        if history[-1]["tick"] == current["tick"]:
            history = history[:-1]

        return {
            "paused": simulation_paused,
            "speed": simulation_speed,
            **current,
            "population_history": [*history, current],
        }


def _get_brain_inputs(monkey_id: int):
    monkey = world.get_monkey(monkey_id)

    if monkey is None:
        raise HTTPException(
            status_code=404,
            detail="Monkey not found",
        )

    observations = (
        world.get_visible_fruit_trees(monkey.x, monkey.y, VISION_RANGE),
        world.get_visible_monkeys(monkey.id, monkey.x, monkey.y, VISION_RANGE),
        world.get_visible_tourists(monkey.x, monkey.y, VISION_RANGE),
    )
    state = monkey._get_brain_state(world, *observations)
    return monkey, state, observations


@app.get("/monkeys/{monkey_id}/brain-state")
def get_monkey_brain_state(monkey_id: int):
    with world.lock:
        monkey, state, _ = _get_brain_inputs(monkey_id)
        return {"monkey_id": monkey.id, "brain_state": state}

@app.get("/monkeys/{monkey_id}/brain-output")
def get_monkey_brain_output(monkey_id: int):
    with world.lock:
        monkey, state, _ = _get_brain_inputs(monkey_id)
        outputs = monkey._get_brain_output(state)
        return {"monkey_id": monkey.id, "outputs": outputs.tolist()}

@app.get("/monkeys/{monkey_id}/brain-choice")
def get_monkey_brain_choice(monkey_id: int):
    with world.lock:
        monkey, state, observations = _get_brain_inputs(monkey_id)
        return {
            "monkey_id": monkey.id,
            "valid_actions": monkey._get_valid_actions(world, *observations),
            "chosen_action": monkey._choose_brain_action(world, state, *observations),
        }

@app.get("/monkeys/{monkey_id}/brain-debug")
def get_monkey_brain_debug(monkey_id: int):
    monkey = world.get_monkey(monkey_id)

    if monkey is None:
        raise HTTPException(
            status_code=404,
            detail="Monkey not found",
        )

    return {
        "id": monkey.id,
        "hunger": monkey.hunger,
        "brain_experiences": len(
            monkey.brain_experiences
        ),
        "training_loss": monkey.last_training_loss,
        "q_values": get_controlled_q_values(
            monkey,
            world,
        ),
    }

@app.get("/world/trees")
def get_tree_states():
    return [
        {
            "x": tree.x,
            "y": tree.y,
            "fruit": tree.fruit,
            "max_fruit": tree.max_fruit,
        }
        for tree in world.trees.values()
        if tree.alive
    ]
