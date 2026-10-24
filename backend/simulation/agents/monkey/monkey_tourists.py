
import random

from backend.simulation.agents.monkey.monkey_constants import (
    VISION_RANGE,
    SOCIAL_MEMORY_RECENCY_TICKS,
    TOURIST_INTERACTION_COOLDOWN_TICKS,
    WANDER_STATE,
)


# ============================================================
# TOURIST OBSERVATION
# ============================================================

def observe_tourists(monkey, world):
    visible_tourists = world.get_visible_tourists(
        monkey.x,
        monkey.y,
        VISION_RANGE,
    )

    for tourist in visible_tourists:
        visible_items = [
            item.name for item in tourist.items
        ]

        monkey.social_memory.remember_tourist(
            tourist.id,
            tourist.x,
            tourist.y,
            world.total_tick,
            visible_items,
        )

    return visible_tourists


# ============================================================
# TARGET SELECTION
# ============================================================

def choose_tourist_to_investigate(monkey, world):
    memory = monkey.social_memory.known_tourists
    cutoff = world.total_tick - SOCIAL_MEMORY_RECENCY_TICKS

    # Keep the existing tourist while its memory is recent.
    if monkey.target_tourist_id is not None:
        remembered = memory.get(monkey.target_tourist_id)

        if (
            remembered is not None
            and remembered.last_seen_tick is not None
            and remembered.last_seen_tick >= cutoff
        ):
            return remembered

        # Existing target is no longer remembered.
        monkey.target_tourist_id = None
        monkey._clear_movement_target()

    # Cooldown prevents acquiring a new tourist.
    if monkey.tourist_interaction_cooldown > 0:
        return None

    candidates = [
        remembered
        for remembered in memory.values()
        if (
            remembered.last_seen_tick is not None
            and remembered.last_seen_tick >= cutoff
        )
    ]

    if not candidates:
        return None

    chosen = random.choice(candidates)

    monkey.target_tourist_id = chosen.tourist_id
    monkey._clear_movement_target()

    return chosen


def get_target_tourist(monkey, world, visible_tourists=None):
    """
    Return the selected tourist if currently visible.

    Does not automatically replace the selected tourist
    with another nearby tourist.
    """
    if monkey.target_tourist_id is None:
        return None

    if visible_tourists is None:
        visible_tourists = world.get_visible_tourists(
            monkey.x,
            monkey.y,
            VISION_RANGE,
        )

    return next(
        (
            tourist
            for tourist in visible_tourists
            if tourist.id == monkey.target_tourist_id
        ),
        None,
    )


# ============================================================
# INVESTIGATE TOURIST
# ============================================================

def handle_tourist_investigation(
    monkey,
    world,
    visible_tourists,
):
    remembered = choose_tourist_to_investigate(
        monkey,
        world,
    )

    if remembered is None:
        return False

    monkey.state = "investigating_tourist"
    monkey.target_monkey_id = None

    tourist = get_target_tourist(
        monkey,
        world,
        visible_tourists,
    )

    if tourist is not None:
        distance = monkey._chebyshev_distance(
            tourist.x,
            tourist.y,
        )

        # Close enough to interact on a subsequent tick.
        if distance <= 3:
            monkey._clear_movement_target()
            return True

        destination = (tourist.x, tourist.y)

    else:
        # The tourist is out of sight.
        # Search its last remembered location.
        destination = (
            remembered.last_x,
            remembered.last_y,
        )

        # Reached the remembered location but tourist absent.
        if (monkey.x, monkey.y) == destination:
            monkey.target_tourist_id = None
            monkey._clear_movement_target()
            monkey.state = WANDER_STATE
            return False

    # Recalculate the path only if the destination changes.
    if (
        monkey.target_x,
        monkey.target_y,
    ) != destination:
        monkey.set_target(
            world,
            destination[0],
            destination[1],
        )

    monkey._move_toward_target(world)

    return True


# ============================================================
# INDIVIDUAL TOURIST ACTIONS
# ============================================================

def watch_tourist(monkey, world, tourist):
    if tourist is None:
        return False

    distance = monkey._chebyshev_distance(
        tourist.x,
        tourist.y,
    )

    # Must be close enough to watch.
    if distance > 3:
        return False

    monkey.state = "watching_tourist"

    # Stop walking without forgetting the tourist.
    monkey._clear_movement_target()

    return True


def follow_tourist(monkey, world, tourist):
    if tourist is None:
        return False

    monkey.state = "following_tourist"

    distance = monkey._chebyshev_distance(
        tourist.x,
        tourist.y,
    )

    # Remain close without standing directly on the tourist.
    if distance <= 2:
        monkey._clear_movement_target()
        return True

    destination = (tourist.x, tourist.y)

    if (
        monkey.target_x,
        monkey.target_y,
    ) != destination:
        monkey.set_target(
            world,
            destination[0],
            destination[1],
        )

    monkey._move_toward_target(world)

    return True


def scare_tourist(monkey, world, tourist):
    if tourist is None:
        return False

    distance = monkey._chebyshev_distance(
        tourist.x,
        tourist.y,
    )

    if distance > 3:
        return False

    monkey.state = "scaring_tourist"
    monkey._clear_movement_target()

    # TODO: Add actual tourist fear/reaction logic.
    # Currently records a scare attempt, not a tourist reaction.
    return True


def leave_tourist(monkey, world, tourist=None):
    # Leaving works even if the tourist is no longer visible.
    if monkey.target_tourist_id is None:
        return False

    monkey.state = WANDER_STATE
    monkey.current_tourist_action = None
    monkey.tourist_interaction_ticks = 0

    monkey.tourist_interaction_cooldown = (
        TOURIST_INTERACTION_COOLDOWN_TICKS
    )

    # Explicitly forget the tourist and current movement.
    monkey.clear_target()

    return True


# ============================================================
# GRAB ITEM
# Kept for future development.
# NOT included in the brain action dispatcher.
# ============================================================

def grab_item_monkey(monkey, world, tourist, item):
    return world.transfer_item_to_monkey(
        monkey,
        tourist,
        item,
    )


def grab_tourist_item(monkey, world, tourist):
    if tourist is None or not tourist.items:
        return False

    item = random.choice(tourist.items)

    success = grab_item_monkey(
        monkey,
        world,
        tourist,
        item,
    )

    if success:
        monkey.tourist_interaction_cooldown = (
            TOURIST_INTERACTION_COOLDOWN_TICKS
        )
        monkey.current_tourist_action = None
        monkey.tourist_interaction_ticks = 0
        monkey.clear_target()

    return success

def steal_item(monkey, world, tourist):
    # No tourist or no possessions to steal.
    if tourist is None or not tourist.items:
        return False

    # Stealing requires close proximity.
    distance = monkey._chebyshev_distance(
        tourist.x,
        tourist.y,
    )

    if distance > 3:
        return False

    # Choose one of the tourist's possessions.
    item = random.choice(tourist.items)

    # Transfer ownership using the existing world method.
    success = world.transfer_item_to_monkey(
        monkey,
        tourist,
        item,
    )

    if not success:
        return False

    # If the stolen item is food, consume it immediately.
    if item.kind == "food" and item.hunger_restore:
        if item.kind == "food":
            monkey.held_items.remove(item)

            # Fully satisfy hunger when stealing food.
            monkey.eat(monkey.hunger)

    # Prevent immediately stealing another item.
    monkey.tourist_interaction_cooldown = (
        TOURIST_INTERACTION_COOLDOWN_TICKS
    )

    monkey.current_tourist_action = None
    monkey.tourist_interaction_ticks = 0

    # Forget the current tourist after stealing.
    monkey.clear_target()

    print(
        f"[STEAL SUCCESS] "
        f"monkey={monkey.id} "
        f"tourist={tourist.id} "
        f"item={item.name}",
        flush=True,
    )

    return True
# ============================================================
# BRAIN ACTION DISPATCHER
# ============================================================

TOURIST_ACTION_HANDLERS = {
    "watch_tourist": watch_tourist,
    "follow_tourist": follow_tourist,
    "scare_tourist": scare_tourist,
    "leave_tourist": leave_tourist,
    "steal_item": steal_item,  # NEW
}


def execute_tourist_action(monkey, world, tourist, action):
    """
    Execute an action selected by the main MonkeyBrain.

    All interactions except leave require the selected
    tourist to be currently visible.
    """
    handler = TOURIST_ACTION_HANDLERS.get(action)

    monkey.last_tourist_action = action
    monkey.current_tourist_action = action
    monkey.last_tourist_action_success = False

    if handler is None:
        monkey.current_tourist_action = None
        return False

    # Leaving does not require current visibility.
    if action != "leave_tourist":
        if (
            tourist is None
            or tourist.id != monkey.target_tourist_id
        ):
            return False

    success = bool(
        handler(monkey, world, tourist)
    )

    monkey.last_tourist_action_success = success

    if action == "leave_tourist":
        monkey.current_tourist_action = None

    return success


# ============================================================
# TOURIST COOLDOWN
# ============================================================

def update_tourist_interaction_cooldown(monkey):
    if monkey.tourist_interaction_cooldown > 0:
        monkey.tourist_interaction_cooldown -= 1

