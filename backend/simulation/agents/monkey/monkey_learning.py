
import torch
import random
import torch.nn.functional as F

from backend.simulation.agents.experience import Experience
from backend.simulation.agents.monkey.monkey_constants import (
    MONKEY_ACTIONS,
    TOURIST_ACTIONS,
    VISION_RANGE,
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
)





def get_valid_actions(monkey, world):
    valid_actions = ["wander"]

    visible_food = world.get_visible_fruit_trees(monkey.x, monkey.y, VISION_RANGE)
    if visible_food or monkey.food_memory:
        valid_actions.append("seek_food")

    if monkey.should_follow_mother():
        valid_actions.append("follow_mother")

    if monkey.energy <= SLEEP_ENERGY_THRESHOLD:
        valid_actions.append("seek_shelter")

    visible_monkeys = world.get_visible_monkeys(monkey.id, monkey.x, monkey.y, VISION_RANGE)
    if visible_monkeys:
        valid_actions.extend([
            "approach_monkey",
            "avoid_monkey",
            "follow_monkey",
            "confront_monkey",
            "socialise",
        ])
    visible_tourists = world.get_visible_tourists(monkey.x, monkey.y, VISION_RANGE)
    if visible_tourists:
        valid_actions.extend([
            "investigate_tourist",
            "watch_tourist",
            "follow_tourist",
            "scare_tourist",
            "leave_tourist",
        ])
        if any(tourist.items for tourist in visible_tourists):
            valid_actions.append("grab_item")


    return valid_actions

def calculate_reward(monkey, previous_health, previous_energy, previous_hunger):
    hunger_change = previous_hunger - monkey.hunger
    health_change = monkey.health - previous_health
    energy_change = monkey.energy - previous_energy

    reward = (
        hunger_change * HUNGER_REWARD_WEIGHT
        + health_change * HEALTH_REWARD_WEIGHT
        + energy_change * ENERGY_REWARD_WEIGHT
    )

    return reward

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

def get_brain_state(monkey, world):
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

        # food stuff here
    if visible_food:
        nearest_food = min(
            visible_food,
            key= lambda tree: monkey._chebyshev_distance(tree.x, tree.y)
        )

        food_distance = monkey._chebyshev_distance(
            nearest_food.x,
            nearest_food.y,
        )

        food_visible = 1.0
        food_distance_normalized = min(food_distance, VISION_RANGE) / VISION_RANGE
    else:
        food_visible = 0.0
        food_distance_normalized = 1.0


        # monkey stuff here
    if visible_monkeys:
        nearest_monkey = min(
            visible_monkeys,
            key=lambda other: monkey._chebyshev_distance(
                other.x,
                other.y,
            )
        )
        monkey_distance = monkey._chebyshev_distance(
            nearest_monkey.x,
            nearest_monkey.y,
        )

        monkey_visible = 1.0
        monkey_distance_normalized = min(monkey_distance, VISION_RANGE) / VISION_RANGE
    else:
        monkey_visible = 0.0
        monkey_distance_normalized = 1.0

        # tourist stuff here
    if visible_tourists:
        nearest_tourist = min(
            visible_tourists,
            key=lambda tourist: monkey._chebyshev_distance(
                tourist.x,
                tourist.y,
            ),
        )

        tourist_distance = monkey._chebyshev_distance(
            nearest_tourist.x,
            nearest_tourist.y,
        )

        tourist_visible = 1.0
        tourist_distance_normalized = min(
            tourist_distance,
            VISION_RANGE,
        ) / VISION_RANGE

        tourist_has_items = (
            1.0
            if nearest_tourist.items
            else 0.0
        )

    else:
        tourist_visible = 0.0
        tourist_distance_normalized = 1.0
        tourist_has_items = 0.0

        # now the rest

     
    return [
            # Survival
        monkey.hunger / MAX_HUNGER,
        monkey.energy / MAX_ENERGY,
        monkey.health / MAX_HEALTH,

            # Genetic traits
        monkey.boldness,
        monkey.curiosity,
        monkey.sociability,
        monkey.memory,
        monkey.aggression,

            # Life stage
        monkey.get_maturity_mod(),

            # Time
        1.0 if world.is_daytime() else 0.0,

            # Food
        food_visible,
        food_distance_normalized,

            # Other monkeys
        monkey_visible,
        monkey_distance_normalized,

            # Tourists
        tourist_visible,
        tourist_distance_normalized,
        tourist_has_items,

            # Inventory
        1.0 if monkey.held_items else 0.0,
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

def choose_brain_action(monkey,state,world):
    outputs = get_brain_output(monkey,state,)

    valid_actions = get_valid_actions(monkey,world,)

    brain_actions = [
        action
        for action in valid_actions
        if action in BRAIN_CONTROLLED_ACTIONS
    ]

    if random.random() < EPSILON:
        return random.choice(brain_actions)

    best_action = None
    best_score = float("-inf")

    for action in brain_actions:
        action_index = encode_monkey_action(action)

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

    next_state = get_brain_state(
        monkey,
        world,
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
    state = get_brain_state(
        monkey,
        world,
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