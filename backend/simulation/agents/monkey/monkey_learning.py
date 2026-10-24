import torch
import random
import torch.nn.functional as F
from backend.simulation.agents.experience import Experience
from backend.simulation.agents.monkey.monkey_constants import (
    MONKEY_ACTIONS,
    TOURIST_ACTIONS,
    VISION_RANGE,
    SOCIAL_MEMORY_RECENCY_TICKS,
    SLEEP_ENERGY_THRESHOLD,
    MAX_HUNGER,
    MAX_ENERGY,
    MAX_HEALTH,
    HUNGER_REWARD_WEIGHT,
    ENERGY_REWARD_WEIGHT,
    HEALTH_REWARD_WEIGHT,
    MAX_EXPERIENCES,
    EPSILON,
    BRAIN_CONTROLLED_ACTIONS,
    LEARNING_RATE,
    GAMMA,
    BATCH_SIZE,
    MIN_TRAINING_EXPERIENCES,
    SURVIVAL_LEARNING_DAYS,
    BASIC_SOCIAL_LEARNING_DAYS,
    TOURIST_LEARNING_DAYS,
)
def get_curriculum_actions(day):
    if day < SURVIVAL_LEARNING_DAYS:
        return {"wander", "seek_food", "seek_shelter"}

    if day < BASIC_SOCIAL_LEARNING_DAYS:
        return {"wander", "seek_food", "seek_shelter",
                "approach_monkey", "follow_monkey"}

    if day < TOURIST_LEARNING_DAYS:
        return {"wander", "seek_food", "seek_shelter",
                "approach_monkey", "follow_monkey", "avoid_monkey",
                "confront_monkey", "socialise"}

    return set(BRAIN_CONTROLLED_ACTIONS) - {"grab_item"}

def get_valid_actions(
    monkey,
    world,
    visible_food,
    visible_monkeys,
    visible_tourists,
):
    valid_actions = ["wander"]

    # ---------------------------------------------------------
    # Survival actions
    # ---------------------------------------------------------

    if visible_food or monkey.food_memory:
        valid_actions.append("seek_food")

    if monkey.should_follow_mother():
        valid_actions.append("follow_mother")

    if monkey.energy <= SLEEP_ENERGY_THRESHOLD:
        valid_actions.append("seek_shelter")

    # ---------------------------------------------------------
    # Monkey social actions
    # ---------------------------------------------------------

    if visible_monkeys:
        valid_actions.extend([
            "approach_monkey",
            "avoid_monkey",
            "follow_monkey",
            "confront_monkey",
            "socialise",
        ])

    # ---------------------------------------------------------
    # Tourist actions
    # ---------------------------------------------------------

    # Find the selected tourist among currently visible tourists.
    # Do not substitute another tourist for the selected target.
    selected_tourist = next(
        (
            tourist
            for tourist in visible_tourists
            if tourist.id == monkey.target_tourist_id
        ),
        None,
    )

    if monkey.target_tourist_id is None:

        # A monkey must investigate before interacting.
        # Cooldown prevents selecting a new tourist.
        if monkey.tourist_interaction_cooldown <= 0:

            # Check whether the monkey remembers a recent tourist.
            recent_tourist = any(
                record.last_seen_tick is not None
                and record.last_seen_tick
                >= world.total_tick - SOCIAL_MEMORY_RECENCY_TICKS
                for record in monkey.social_memory.known_tourists.values()
            )

            # Investigation is available if a tourist is visible
            # or remembered recently.
            if visible_tourists or recent_tourist:
                valid_actions.append("investigate_tourist")

    else:

        # A target is already selected.
        # Investigation remains possible even when it is out of sight.
        valid_actions.append("investigate_tourist")

        # The monkey can always abandon its existing target.
        valid_actions.append("leave_tourist")

        # Interactions require the SELECTED tourist to be visible.
        if selected_tourist is not None:

            distance = monkey._chebyshev_distance(
                selected_tourist.x,
                selected_tourist.y,
            )

            # Follow is valid from any visible distance.
            valid_actions.append("follow_tourist")

            # Watch and scare require the tourist to be nearby.
            if distance <= 3:
                valid_actions.extend([
                    "watch_tourist",
                    "scare_tourist",
                ])

            if (
                distance <= 3
                and selected_tourist.items
                and monkey.tourist_interaction_cooldown <= 0
            ):
                valid_actions.append("steal_item")

    # ---------------------------------------------------------
    # Curriculum filtering
    # ---------------------------------------------------------

    allowed_actions = get_curriculum_actions(world.day)

    return [
        action
        for action in valid_actions
        if action in MONKEY_ACTIONS
        and action != "grab_item"
        and (
            action not in BRAIN_CONTROLLED_ACTIONS
            or action in allowed_actions
        )
    ]

def calculate_reward(
    monkey,
    previous_health,
    previous_energy,
    previous_hunger,
    tourist_action=None,
    tourist_success=False,
    reached_tourist=False,
):
    # -------------------------------------
    # Survival reward
    # -------------------------------------

    hunger_change = previous_hunger - monkey.hunger
    health_change = monkey.health - previous_health
    energy_change = monkey.energy - previous_energy

    hunger_need = previous_hunger / MAX_HUNGER

    survival_reward = (
        hunger_change * HUNGER_REWARD_WEIGHT * hunger_need
        + health_change * HEALTH_REWARD_WEIGHT
        + energy_change * ENERGY_REWARD_WEIGHT
    )

    # -------------------------------------
    # Tourist behaviour reward
    # -------------------------------------

    tourist_reward = 0.0

    if tourist_action == "investigate_tourist":
        # Reward reaching interaction range,
        # not merely choosing to investigate.
        if reached_tourist:
            tourist_reward += 0.3

    elif tourist_action == "watch_tourist":
        if tourist_success:
            tourist_reward += 0.1

    elif tourist_action == "follow_tourist":
        if tourist_success:
            tourist_reward += 0.2

    elif tourist_action == "scare_tourist":
        # For now, only a small reward for a valid attempt.
        # Increase once tourists actually react.
        if tourist_success:
            tourist_reward += 0.1

    elif tourist_action == "leave_tourist":
        # Leaving should not automatically be rewarded or punished.
        tourist_reward += 0.0

    # Penalise invalid interactions.
    if (
        tourist_action is not None
        and tourist_action != "leave_tourist"
        and not tourist_success
    ):
        tourist_reward -= 0.2

    return survival_reward + tourist_reward


def encode_tourist_action(action):
    return TOURIST_ACTIONS.index(action)
def encode_monkey_action(action):
    return MONKEY_ACTIONS.index(action)
def finalize_tourist_experience(monkey, world):
    if (
        monkey.pending_tourist_state is None
        or monkey.pending_tourist_action is None
        or monkey.pending_tourist_id is None
    ):
            return
    tourist = world.get_tourist(monkey.pending_tourist_id)
    if tourist is not None:
        next_state = monkey._get_tourist_state(tourist)
    else:
        next_state = monkey.pending_tourist_state.copy()
    experience = Experience(
        state=monkey.pending_tourist_state,
        action=monkey.pending_tourist_action,
        reward=monkey.pending_tourist_reward,
        next_state=next_state,
    )
    monkey.experiences.append(experience)
    if len(monkey.experiences) > MAX_EXPERIENCES:
        monkey.experiences.pop(0)
    monkey.pending_tourist_state = None
    monkey.pending_tourist_action = None
    monkey.pending_tourist_id = None
    monkey.pending_tourist_reward = 0.0
    monkey.pending_tourist_done = False
def get_brain_state(monkey, world, visible_food, visible_monkeys, visible_tourists):
    if visible_food:
        nearest_food = min(
            visible_food,
            key=lambda tree: monkey._chebyshev_distance(tree.x, tree.y),
        )
        food_visible = 1.0
        food_distance_normalized = min(
            monkey._chebyshev_distance(nearest_food.x, nearest_food.y),
            VISION_RANGE,
        ) / VISION_RANGE
    else:
        food_visible = 0.0
        food_distance_normalized = 1.0

    if visible_monkeys:
        nearest_monkey = min(
            visible_monkeys,
            key=lambda other: monkey._chebyshev_distance(other.x, other.y),
        )
        monkey_visible = 1.0
        monkey_distance_normalized = min(
            monkey._chebyshev_distance(nearest_monkey.x, nearest_monkey.y),
            VISION_RANGE,
        ) / VISION_RANGE
    else:
        monkey_visible = 0.0
        monkey_distance_normalized = 1.0

    has_tourist_target = float(monkey.target_tourist_id is not None)
    if monkey.target_tourist_id is not None:
        # Don't substitute another nearby tourist for the selected target.
        observed_tourist = next(
            (tourist for tourist in visible_tourists
             if tourist.id == monkey.target_tourist_id),
            None,
        )
    else:
        observed_tourist = min(
            visible_tourists,
            key=lambda tourist: monkey._chebyshev_distance(tourist.x, tourist.y),
            default=None,
        )

    if observed_tourist is not None:
        tourist_visible = 1.0
        tourist_distance_normalized = min(
            monkey._chebyshev_distance(observed_tourist.x, observed_tourist.y),
            VISION_RANGE,
        ) / VISION_RANGE
        tourist_has_items = float(bool(observed_tourist.items))
    else:
        tourist_visible = 0.0
        tourist_distance_normalized = 1.0
        tourist_has_items = 0.0

    return [
        monkey.hunger / MAX_HUNGER,
        monkey.energy / MAX_ENERGY,
        monkey.health / MAX_HEALTH,
        monkey.boldness,
        monkey.curiosity,
        monkey.sociability,
        monkey.memory,
        monkey.aggression,
        monkey.get_maturity_mod(),
        1.0 if world.is_daytime() else 0.0,
        food_visible,
        food_distance_normalized,
        monkey_visible,
        monkey_distance_normalized,
        tourist_visible,
        tourist_distance_normalized,
        tourist_has_items,
        1.0 if monkey.held_items else 0.0,
        has_tourist_target,  # NEW FEATURE 19: change MonkeyBrain input_size to 19.
    ]

def get_brain_output(monkey, state):
    state_tensor = torch.tensor(
        state,
        dtype=torch.float32,
    )
    with torch.no_grad():
        outputs = monkey.brain(
            state_tensor
        )
    return outputs
def choose_brain_action(
    monkey,
    state,
    valid_actions,
):
    outputs = get_brain_output(
        monkey,
        state,
    )
    brain_actions = [
        action
        for action in valid_actions
        if action in BRAIN_CONTROLLED_ACTIONS
    ]
    if not brain_actions:
        return "wander"

    # TEMPORARY: Prefer stealing during testing.
    DEBUG_FAVOUR_STEALING = True

    if (
        DEBUG_FAVOUR_STEALING
        and "steal_item" in brain_actions
        and random.random() < 0.5
    ):
        return "steal_item"

    # Normal epsilon-greedy selection.
    if random.random() < EPSILON:
        return random.choice(brain_actions)
    
    best_action = None
    best_score = float("-inf")
    for action in brain_actions:
        action_index = encode_monkey_action(
            action
        )
        score = outputs[action_index].item()
        if score > best_score:
            best_score = score
            best_action = action
    return best_action
def finalize_brain_experience(monkey, world):
    if (
        monkey.pending_brain_state is None
        or monkey.pending_brain_action is None
    ):
        return
    visible_food = world.get_visible_fruit_trees(
        monkey.x,
        monkey.y,
        VISION_RANGE,
    )
    visible_monkeys = world.get_visible_monkeys(
        monkey.id,
        monkey.x,
        monkey.y,
        VISION_RANGE,
    )
    visible_tourists = world.get_visible_tourists(
        monkey.x,
        monkey.y,
        VISION_RANGE,
    )
    next_state = get_brain_state(
        monkey,
        world,
        visible_food,
        visible_monkeys,
        visible_tourists,
    )
    experience = Experience(
        state=monkey.pending_brain_state,
        action=monkey.pending_brain_action,
        reward=monkey.reward,
        next_state=next_state,
        done=not monkey.alive,
    )
    monkey.brain_experiences.append(experience)
    if len(monkey.brain_experiences) > MAX_EXPERIENCES:
        monkey.brain_experiences.pop(0)
    monkey.pending_brain_state = None
    monkey.pending_brain_action = None
def train_brain(monkey):
    if (
        len(monkey.brain_experiences)
        < MIN_TRAINING_EXPERIENCES
    ):
        return None
    batch = random.sample(
        monkey.brain_experiences,
        BATCH_SIZE,
    )
    states = torch.tensor(
        [experience.state for experience in batch],
        dtype=torch.float32,
    )
    actions = torch.tensor(
        [experience.action for experience in batch],
        dtype=torch.long,
    )
    rewards = torch.tensor(
        [experience.reward for experience in batch],
        dtype=torch.float32,
    )
    next_states = torch.tensor(
        [experience.next_state for experience in batch],
        dtype=torch.float32,
    )
    dones = torch.tensor(
        [experience.done for experience in batch],
        dtype=torch.float32,
    )
    # Current Q-values predicted by the brain.
    q_values = monkey.brain(states)
    # Keep only the Q-value for the action
    # the monkey actually chose.
    chosen_q_values = q_values.gather(
        1,
        actions.unsqueeze(1),
    ).squeeze(1)
    controlled_indexes = torch.tensor(
        [
            encode_monkey_action(action)
            for action in BRAIN_CONTROLLED_ACTIONS
        ],
        dtype=torch.long,
    )
    # Work out the training target.
    # No gradients are needed for this calculation.
    with torch.no_grad():
        next_q_values = monkey.brain(
            next_states
        )
        controlled_next_q_values = (
            next_q_values[
                :,
                controlled_indexes,
            ]
        )
        best_next_q_values = (
            controlled_next_q_values
            .max(dim=1)
            .values
        )
        targets = rewards + (
            GAMMA
            * best_next_q_values
            * (1.0 - dones)
        )
    loss = F.mse_loss(
        chosen_q_values,
        targets,
    )
    monkey.brain.optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(
        monkey.brain.parameters(),
        max_norm=1.0,
    )
    monkey.brain.optimizer.step()
    return loss.item()
def get_controlled_q_values(monkey, world):
    visible_food = world.get_visible_fruit_trees(
        monkey.x,
        monkey.y,
        VISION_RANGE,
    )
    visible_monkeys = world.get_visible_monkeys(
        monkey.id,
        monkey.x,
        monkey.y,
        VISION_RANGE,
    )
    visible_tourists = world.get_visible_tourists(
        monkey.x,
        monkey.y,
        VISION_RANGE,
    )
    state = get_brain_state(
        monkey,
        world,
        visible_food,
        visible_monkeys,
        visible_tourists,
    )
    outputs = get_brain_output(
        monkey,
        state,
    )
    return {
        action: outputs[
            encode_monkey_action(action)
        ].item()
        for action in BRAIN_CONTROLLED_ACTIONS
    }
