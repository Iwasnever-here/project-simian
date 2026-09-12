
import random

from backend.simulation.agents.monkey.monkey_constants import (
    VISION_RANGE,
    SOCIAL_MEMORY_RECENCY_TICKS,
    TOURIST_INTERACTION_DURATION,
    TOURIST_INTERACTION_COOLDOWN_TICKS,
    WANDER_STATE,
    MAX_HUNGER,
    MAX_ENERGY,
    MAX_HEALTH,
)

from backend.simulation.agents.monkey.monkey_learning import (
    encode_tourist_action,
)

def observe_tourists(monkey, world):
    visible_tourists = world.get_visible_tourists(
        monkey.x,
        monkey.y,
        VISION_RANGE,
    )

    for tourist in visible_tourists:
        visible_items = [
            item.name
            for item in tourist.items
        ]

        monkey.social_memory.remember_tourist(
            tourist.id,
            tourist.x,
            tourist.y,
            world.total_tick,
            visible_items,
        )

    return visible_tourists



def choose_tourist_to_investigate(monkey, world):
    if monkey.tourist_interaction_cooldown > 0:
        return None
        # Keep investigating the current target if the memory is still recent.
    if monkey.target_tourist_id is not None:
        remembered_tourist = monkey.social_memory.known_tourists.get(
            monkey.target_tourist_id
        )

        if remembered_tourist is not None:
            if (
                remembered_tourist.last_seen_tick
                >= world.total_tick - SOCIAL_MEMORY_RECENCY_TICKS
                and remembered_tourist.visible_items
            ):
                return remembered_tourist

        monkey.target_tourist_id = None

    candidates = []

    for remembered_tourist in monkey.social_memory.known_tourists.values():
        if remembered_tourist.last_seen_tick is None:
            continue

        if remembered_tourist.last_seen_tick < (
            world.total_tick - SOCIAL_MEMORY_RECENCY_TICKS
        ):
            continue

        if not remembered_tourist.visible_items:
            continue

        candidates.append(remembered_tourist)

    if not candidates:
        return None

    chosen = random.choice(candidates)

    monkey.target_tourist_id = chosen.tourist_id

    return chosen

def handle_tourist_investigation(
    monkey,
    world,
    visible_tourists,
):
    remembered_tourist = choose_tourist_to_investigate(
        monkey,
        world
    )

    if remembered_tourist is None:
        return False

    monkey.state = "investigating_tourist"
    monkey.target_monkey_id = None

        # Check whether the remembered tourist is currently visible.
    visible_tourist = next(
        (
            tourist
            for tourist in visible_tourists
            if tourist.id == remembered_tourist.tourist_id
        ),
        None,
    )

        # -------------------------------------------------------------
        # Tourist is currently visible
        # -------------------------------------------------------------
    if visible_tourist is not None:
        distance = monkey._chebyshev_distance(
            visible_tourist.x,
            visible_tourist.y,
        )

            # Close enough to decide how to interact.
        if distance <= 3:
            monkey._clear_movement_target()

            handle_tourist_interactions(
                monkey,
                world,
                visible_tourist,
            )

            return True

            # Tourist has moved, so follow their current position.
        if (
            monkey.target_x != visible_tourist.x
            or monkey.target_y != visible_tourist.y
        ):
            monkey.set_target(
                world,
                visible_tourist.x,
                visible_tourist.y,
            )

        monkey._move_toward_target(world)

        return True

        # -------------------------------------------------------------
        # Tourist is no longer visible
        # -------------------------------------------------------------

        # Move toward the last place the monkey remembers seeing them.
    if (
        monkey.target_x != remembered_tourist.last_x
        or monkey.target_y != remembered_tourist.last_y
    ):
        monkey.set_target(
            world,
            remembered_tourist.last_x,
            remembered_tourist.last_y,
        )

        # We reached their remembered location and they aren't there.
    if monkey._is_at_target():
        monkey.clear_target()
        monkey.state = WANDER_STATE
        monkey.current_tourist_action = None
        monkey.pending_tourist_done = True

        return False

    monkey._move_toward_target(world)

    return True

def handle_tourist_interactions(monkey, world, tourist):
    if monkey.tourist_interaction_ticks == 0:
        monkey.tourist_interaction_ticks = TOURIST_INTERACTION_DURATION

    if monkey.current_tourist_action is None:
        monkey.current_tourist_action = choose_tourist_action(tourist)

        monkey.pending_tourist_state = get_tourist_state(monkey, tourist)
        monkey.pending_tourist_action = encode_tourist_action(
            monkey.current_tourist_action
        )
        monkey.pending_tourist_id = tourist.id
        monkey.pending_tourist_reward = 0.0
        monkey.pending_tourist_done = False

    return execute_tourist_action(
        monkey,
        world,
        tourist,
        monkey.current_tourist_action,
    )

def update_tourist_interaction_ticks(monkey):
    if monkey.tourist_interaction_ticks > 0:
        monkey.tourist_interaction_ticks -= 1

    if monkey.tourist_interaction_ticks <= 0:
        monkey.pending_tourist_done = True

        monkey.state = WANDER_STATE
        monkey.current_tourist_action = None
        monkey.pending_tourist_done = True
        monkey.tourist_interaction_cooldown = TOURIST_INTERACTION_COOLDOWN_TICKS
        monkey.clear_target()

        return False

    return True

def update_tourist_interaction_cooldown(monkey):
    if monkey.tourist_interaction_cooldown > 0:
        monkey.tourist_interaction_cooldown -= 1



def grab_item_monkey(monkey, world, tourist, item):
    return world.transfer_item_to_monkey(
        monkey,
        tourist,
        item,
    )


def choose_tourist_action(tourist):
    actions = [
        "watch",
        "follow",
        "scare",
        "leave"
    ]

    if tourist.items:
        actions.append("grab_item")

    return random.choice(actions)

def execute_tourist_action(monkey, world, tourist, action):
    monkey.last_tourist_action = action

    if action == "watch":
        monkey.state = "watching_tourist"
        monkey._clear_movement_target()
        monkey.last_tourist_action_success = True
        return True

    if action == "follow":
        monkey.state = "following_tourist"

        if (
            monkey.target_x != tourist.x
            or monkey.target_y != tourist.y
        ):
            monkey.set_target(
                world,
                tourist.x,
                tourist.y,
            )

        monkey._move_toward_target(world)
        monkey.last_tourist_action_success = True
        return True

    if action == "scare":
        monkey.state = "scaring_tourist"
        monkey.last_tourist_action_success = True
        return True

    if action == "grab_item":
        if not tourist.items:
            monkey.last_tourist_action_success = False
            monkey.current_tourist_action = None
            return False

        item = random.choice(tourist.items)

        success = grab_item_monkey(
            monkey,
            world,
            tourist,
            item,
        )

        monkey.last_tourist_action_success = success

        monkey.pending_tourist_done = True

        monkey.current_tourist_action = None
        monkey.tourist_interaction_ticks = 0
        monkey.tourist_interaction_cooldown = (
            TOURIST_INTERACTION_COOLDOWN_TICKS
        )
        monkey.clear_target()

        return success

    if action == "leave":
        monkey.state = WANDER_STATE
        monkey.current_tourist_action = None
        monkey.tourist_interaction_ticks = 0
        monkey.tourist_interaction_cooldown = (
            TOURIST_INTERACTION_COOLDOWN_TICKS
        )
        monkey.clear_target()

        monkey.pending_tourist_done = True

        monkey.last_tourist_action_success = True
        return False


def get_tourist_state(monkey, tourist):
    distance = monkey._chebyshev_distance(
        tourist.x,
        tourist.y,
    )

    return [
        monkey.hunger / MAX_HUNGER,
        monkey.energy / MAX_ENERGY,
        monkey.health / MAX_HEALTH,

        monkey.boldness,
        monkey.curiosity,
        monkey.aggression,

        min(distance, VISION_RANGE) / VISION_RANGE,
        min(len(tourist.items), 5) / 5.0,
    ]
    