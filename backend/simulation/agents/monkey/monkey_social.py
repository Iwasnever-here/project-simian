from backend.simulation.agents.monkey.monkey_constants import (
    VISION_RANGE,
    SOCIAL_MEMORY_RECENCY_TICKS,
    MIN_SOCIAL_DISTANCE,
    MAX_SOCIAL_DISTANCE,
    SOCIAL_DISTANCE_HYSTERESIS,
    SOCIAL_DECISION_TICKS,
    AGGRESSION_DOMINANCE_THRESHOLD,
    APPROACHING_MONKEY_STATE,
    AVOIDING_MONKEY_STATE,
    FOLLOWING_MONKEY_STATE,
    CONFRONTING_MONKEY_STATE,
    SOCIAL_IDLE_STATE,
)


def observe_monkeys(monkey, world):
    visible_monkeys = world.get_visible_monkeys(
        monkey.id,
        monkey.x,
        monkey.y,
        VISION_RANGE,
    )

    for other in visible_monkeys:
        monkey.social_memory.remember(
            other.id,
            other.x,
            other.y,
            world.total_tick,
        )

    return visible_monkeys


def choose_social_target (monkey, visible_monkeys,current_tick,):
    known_recent = [other for other in visible_monkeys
        if (record := monkey.social_memory.get(other.id)) is not None
        and current_tick - record.last_seen_tick <= SOCIAL_MEMORY_RECENCY_TICKS
    ]

    candidates = (known_recent if known_recent else visible_monkeys)

    return min(
        candidates,
        key=lambda other:monkey._chebyshev_distance(other.x,other.y,),
    )


def desired_social_distance(monkey, other):
    base = MIN_SOCIAL_DISTANCE + (1.0 - monkey.sociability) * (
        MAX_SOCIAL_DISTANCE- MIN_SOCIAL_DISTANCE)

    threat = other.aggression
    confidence = monkey.aggression

    base += threat * 1.5
    base -= confidence * 1.5

    return max(
        MIN_SOCIAL_DISTANCE,
        min(MAX_SOCIAL_DISTANCE, base, ),
    )

def approach_monkey( monkey, world,visible_monkeys,):
    if not visible_monkeys:
        return False

    other = choose_social_target(
        monkey,
        visible_monkeys,
        world.total_tick,
    )

    monkey.state = APPROACHING_MONKEY_STATE
    monkey.target_monkey_id = other.id

    distance = monkey._chebyshev_distance(  other.x, other.y,)

    if distance <= MIN_SOCIAL_DISTANCE:
        monkey._clear_movement_target()
        return True

    monkey._clear_movement_target()

    monkey.set_target(world, other.x, other.y,)

    monkey._move_toward_target(world)

    return True


def follow_monkey( monkey, world, visible_monkeys,):
    if not visible_monkeys:
        return False

    # Keep following the same monkey if it is still visible.
    other = None

    if monkey.target_monkey_id is not None:
        other = next(
            (
                candidate
                for candidate in visible_monkeys
                if candidate.id
                == monkey.target_monkey_id
            ),
            None,
        )

    # Otherwise choose a new target.
    if other is None:
        other = choose_social_target(
            monkey,
            visible_monkeys,
            world.total_tick,
        )

        monkey.target_monkey_id = other.id

    monkey.state = FOLLOWING_MONKEY_STATE

    distance = monkey._chebyshev_distance(
        other.x,
        other.y,
    )

    # Don't stand directly on top of the target.
    if distance <= MIN_SOCIAL_DISTANCE:
        monkey._clear_movement_target()
        return True

    # Target may have moved since last tick.
    monkey._clear_movement_target()

    monkey.set_target(world, other.x, other.y,)

    monkey._move_toward_target(world)

    return True


def avoid_monkey( monkey, world, visible_monkeys,):
    if not visible_monkeys:
        return False

    other = choose_social_target(
        monkey,
        visible_monkeys,
        world.total_tick,
    )

    flee_from( monkey, world, other,)

    return True


def confront_monkey(monkey, world, visible_monkeys,):
    if not visible_monkeys:
        return False

    other = choose_social_target(
        monkey,
        visible_monkeys,
        world.total_tick,
    )

    confront( monkey, world, other,)

    return True


def socialise_monkey( monkey, world, visible_monkeys,):
    if not visible_monkeys:
        return False

    other = choose_social_target(
        monkey,
        visible_monkeys,
        world.total_tick,
    )

    monkey.target_monkey_id = other.id

    distance = monkey._chebyshev_distance(
        other.x,
        other.y,
    )

    desired = desired_social_distance( monkey, other,)

    # Too far away: move closer.
    if (
        distance
        > desired + SOCIAL_DISTANCE_HYSTERESIS
    ):
        monkey.state = SOCIAL_IDLE_STATE

        monkey._clear_movement_target()

        monkey.set_target( world, other.x, other.y,)

        monkey._move_toward_target(world)

        return True

    # Too close: create some space.
    if (
        distance
        < desired - SOCIAL_DISTANCE_HYSTERESIS
    ):
        monkey.state = SOCIAL_IDLE_STATE

        monkey._clear_movement_target()

        step_away_from( monkey, world, other,)

        return True

    # Comfortable social distance.
    monkey.state = SOCIAL_IDLE_STATE

    monkey._clear_movement_target()

    return True

def step_away_from(monkey,  world, other,):
    dx = monkey.x - other.x
    dy = monkey.y - other.y

    step_x = ((dx > 0)- (dx < 0))

    step_y = ((dy > 0)- (dy < 0))

    moved = monkey.move(world, monkey.x + step_x, monkey.y + step_y,)

    if moved:
        return

    monkey._wander(world)


def flee_from (monkey,world,other,):
    monkey.state = (AVOIDING_MONKEY_STATE)

    monkey.target_monkey_id = (other.id)

    monkey._clear_movement_target()

    step_away_from(monkey,world,other,)


def confront(monkey,world,other,):
    monkey.state = (CONFRONTING_MONKEY_STATE)

    monkey.target_monkey_id = (other.id)

    distance = monkey._chebyshev_distance(other.x, other.y)

    if distance <= MIN_SOCIAL_DISTANCE:
        monkey._clear_movement_target()
        return

    monkey._clear_movement_target()

    monkey.set_target(world, other.x, other.y,)

    monkey._move_toward_target(world)