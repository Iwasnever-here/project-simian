from dataclasses import dataclass, field
import random


from backend.simulation.agents.monkey.monkey_learning import (
    get_valid_actions,
    calculate_reward,
    encode_tourist_action,
    encode_monkey_action,
    finalize_tourist_experience,
    get_brain_state,
    get_brain_output,
    choose_brain_action,
    finalize_brain_experience,
    train_brain
)

from backend.simulation.agents.monkey.monkey_constants import (
    WANDER_STATE,
    SEEKING_FOOD_STATE,
    EATING_STATE,
    SLEEPING_STATE,
    SEEKING_SHELTER_STATE,
    FOLLOW_MOTHER_STATE,
 

    MONKEY_ACTIONS,
    HUNGER_PER_TICK,
    #FOOD_SEEK_THRESHOLD,
    MAX_HUNGER,
    FRUIT_HUNGER_REDUCTION,
    MAX_FOOD_MEMORIES,
    FOOD_MEMORY_COOLDOWN_TICKS,

    SLEEP_ENERGY_THRESHOLD,
    WAKE_ENERGY_THRESHOLD,
    MAX_ENERGY,
    SLEEP_ENERGY_RECOVERY,
    MOVEMENT_COST,
    IDLE_COST,

    MAX_STARVING_TICK,
    MAX_EXHAUSTED_TICK,
    MAX_AGE_DAYS,
    DAY_SLEEP_RISK,
    NIGHT_SLEEP_RISK,
    DAY_IDLE_RISK,
    NIGHT_IDLE_RISK,
    MOVING_RISK,
    RISK_ENERGY_COST,
    MAX_HEALTH,
    STARVATION_DAMAGE,
    EXHAUST_DAMAGE,

    INFANT_MAX_AGE,
    JUVENILE_MAX_AGE,
    ELDERLY_MIN_AGE,
    MIN_REPRODUCTION_ENERGY,
    MIN_REPRODUCTION_HEALTH,
    REPRODUCTION_COOLDOWN_TICKS,

    TRAIT_MUTATION_STDDEV,

    MIN_TRAIT_VALUE,
    MAX_TRAIT_VALUE,

    VISION_RANGE,
    MOVEMENT_DIRECTIONS,
    MOTHER_FOLLOW_DISTANCE,
    TRAINING_INTERVAL_TICKS,
)

from backend.simulation.agents.monkey.monkey_tourists import (
    observe_tourists,
    choose_tourist_to_investigate,
    handle_tourist_investigation,
    handle_tourist_interactions,
    update_tourist_interaction_ticks,
    update_tourist_interaction_cooldown,
    grab_item_monkey,
    choose_tourist_action,
    execute_tourist_action,
    get_tourist_state,
)

from backend.simulation.agents.monkey.monkey_social import (
    observe_monkeys,
    choose_social_target,
    desired_social_distance,
    handle_social_interaction,
    step_away_from,
    flee_from,
    confront,
)

from backend.simulation.agents.monkeyMemory import MonkeyMemory
from backend.simulation.world import world
from ..touristItem import TouristItem
from ..experience import Experience

from backend.simulation.learning.monkeyBrain import MonkeyBrain



def random_trait() -> float:
    value = random.gauss(0.5, 0.15)

    return max(
        MIN_TRAIT_VALUE,
        min(MAX_TRAIT_VALUE, value),
    )


def inherit_trait(parent_a_trait: float, parent_b_trait: float) -> float:
    inherited = (parent_a_trait + parent_b_trait) / 2.0
    mutation = random.gauss(0.0, TRAIT_MUTATION_STDDEV)
    value = inherited + mutation

    return max(
        MIN_TRAIT_VALUE,
        min(MAX_TRAIT_VALUE, value),
    )


# ---------------------------------------------------------------------
# Vision and movement
# ---------------------------------------------------------------------

@dataclass
class Monkey:
    id: int
    x: int
    y: int
    gender: str
    name: str

    # Core survival stats
    hunger: float = 0.0
    age: int = 0
    health: float = MAX_HEALTH
    energy: float = 100.0
    state: str = WANDER_STATE

    # Reproduction
    parent_ids: tuple[int, int] | None = None
    birth_tick: int = 0
    last_reproduction_tick: int | None = None

    # Genetic traits
    boldness: float = 0.5
    curiosity: float = 0.5
    sociability: float = 0.5
    memory: float = 0.5
    aggression: float = 0.5

    # Target and survival tracking
    target_x: int | None = None
    target_y: int | None = None
    starving_ticks: int = 0
    exhausted_ticks: int = 0
    alive: bool = True
    target_monkey_id: int | None = None
    social_decision_cooldown: int = 0
    tourist_interaction_ticks: int = 0
    tourist_interaction_cooldown: int = 0
    target_tourist_id: int | None = None

    # Memory and pathfinding
    food_memory: list[tuple[int, int]] = field(default_factory=list)
    food_memory_cooldowns: dict[tuple[int, int], int] = field(
        default_factory=dict
    )
    path: list[tuple[int, int]] = field(default_factory=list)

    social_memory: MonkeyMemory = field(default_factory=MonkeyMemory)
    held_items: list[TouristItem] = field(default_factory=list)
    # Per-tick movement state
    moved_this_tick: bool = False
    current_tourist_action: str | None = None
    last_tourist_action: str | None = None
    last_tourist_action_success: bool | None = None

    #neural networks things
    reward: float = 0.0
    experiences: list[Experience] = field(default_factory=list)
    pending_tourist_state: list[float] | None = None
    pending_tourist_action: int | None = None
    pending_tourist_id: int | None = None
    pending_tourist_reward: float = 0.0
    pending_tourist_done: bool = False

    pending_brain_state: list[float] | None = None
    pending_brain_action: int | None = None

    brain_experiences: list[Experience] = field(
        default_factory=list
    )

    last_training_loss: float | None = None

    brain: MonkeyBrain = field(default_factory = lambda: MonkeyBrain(
        input_size = 18,
        output_size = len(MONKEY_ACTIONS)
    ))
    

    # -----------------------------------------------------------------
    # Main update
    # -----------------------------------------------------------------

    def update(self, world):
        previous_hunger = self.hunger
        previous_energy = self.energy
        previous_health = self.health

        if not self.alive:
            return

        self.moved_this_tick = False

        self._increase_hunger()
        self._update_food_memory_cooldowns()
        self._update_tourist_interaction_cooldown()

        if self.state == SLEEPING_STATE:
            self._sleep(world)

        else:
            self.update_awake_energy()

            visible_monkeys = self._observe_monkeys(world)
            visible_tourists = self._observe_tourists(world)

            # Keep emergency sleep hard-coded for now.
            if (
                self.energy <= SLEEP_ENERGY_THRESHOLD
                or self.state == SEEKING_SHELTER_STATE
            ):
                self._handle_seeking_shelter(world)

            elif (
                self.should_follow_mother()
                and self.follow_mother(world)
            ):
                pass

            elif (
                self.target_tourist_id is not None
                and self.state in (
                    "watching_tourist",
                    "following_tourist",
                    "scaring_tourist",
                )
            ):
                if self._update_tourist_interaction_ticks():
                    tourist = next(
                        (
                            tourist
                            for tourist in visible_tourists
                            if tourist.id
                            == self.target_tourist_id
                        ),
                        None,
                    )

                    if tourist is None:
                        self.state = (
                            "investigating_tourist"
                        )
                        self.current_tourist_action = None
                        self.pending_tourist_done = True

                    else:
                        self._handle_tourist_interactions(
                            world,
                            tourist,
                        )

            else:
                # Brain gets control here.
                brain_state = self._get_brain_state(
                    world
                )

                brain_action = self._choose_brain_action(
                    brain_state,
                    world
                )

                self.pending_brain_state = brain_state
                self.pending_brain_action = (
                    self._encode_monkey_action(
                        brain_action
                    )
                )

                if brain_action == "seek_food":
                    self._handle_food_seeking(
                        world
                    )

                elif brain_action == "wander":
                    self.state = WANDER_STATE
                    self.clear_target()
                    self._wander(world)

        self.apply_environmental_risk(world)
        self._update_survival()

        self.reward = self._calculate_reward(
            previous_health,
            previous_energy,
            previous_hunger,
        )

        self._finalize_brain_experience(
            world
        )

        if world.total_tick % TRAINING_INTERVAL_TICKS == 0:
            self.last_training_loss = (
                self._train_brain()
            )

        if self.pending_tourist_state is not None:
            self.pending_tourist_reward += (
                self.reward
            )

        if self.pending_tourist_done:
            self._finalize_tourist_experience(
                world
            )

    # -----------------------------------------------------------------
    # Hunger and food seeking
    # -----------------------------------------------------------------

    def _increase_hunger(self):
        self.hunger = min(
            MAX_HUNGER,
            self.hunger + HUNGER_PER_TICK,
        )

    def _handle_food_seeking(self, world):
        self.state = SEEKING_FOOD_STATE

        if self.target_x is None or self.target_y is None:
            target = self._find_visible_food(world)

            if target is not None:
                self.set_target(
                    world,
                    target.x,
                    target.y,
                )

            else:
                remembered_location = self._find_remembered_food()

                if remembered_location is not None:
                    self.set_target(
                        world,
                        remembered_location[0],
                        remembered_location[1],
                    )

                else:
                    self._wander(world)
                    return

        if self._is_at_target():
            self._eat_from_target(world)
            return

        self._move_toward_target(world)

    def _find_visible_food(self, world):
        trees = world.get_visible_fruit_trees(
            self.x,
            self.y,
            VISION_RANGE,
        )

        if not trees:
            return None

        return min(
            trees,
            key=lambda tree:
                abs(tree.x - self.x)
                + abs(tree.y - self.y),
        )

    def _eat_from_target(self, world):
        if self.target_x is None or self.target_y is None:
            return

        self.state = EATING_STATE

        food_x = self.target_x
        food_y = self.target_y

        harvested = world.harvest_tree_fruit(
            food_x,
            food_y,
            1,
        )

        if harvested <= 0:
            location = (
                food_x,
                food_y,
            )

            if location in self.food_memory:
                self.food_memory_cooldowns[location] = (
                    FOOD_MEMORY_COOLDOWN_TICKS
                )

            self.clear_target()
            self.state = SEEKING_FOOD_STATE
            return

        self.remember_food_location(
            food_x,
            food_y,
        )

        self.eat(
            harvested * FRUIT_HUNGER_REDUCTION,
        )

    def eat(self, food_amount):
        if food_amount <= 0:
            return

        self.hunger = max(
            0.0,
            self.hunger - food_amount,
        )

        self.state = WANDER_STATE
        self.clear_target()

    # -----------------------------------------------------------------
    # Food memory
    # -----------------------------------------------------------------

    def remember_food_location(self, x, y):
        location = (x, y)

        # Already remembered.
        # Move it to the end so it becomes the most recent memory.
        if location in self.food_memory:
            self.food_memory.remove(location)

        self.food_memory.append(location)

        # Forget oldest location if memory is full.
        if len(self.food_memory) > MAX_FOOD_MEMORIES:
            self.food_memory.pop(0)

    def _find_remembered_food(self):
        available_memories = [
            location
            for location in self.food_memory
            if location not in self.food_memory_cooldowns
        ]

        if not available_memories:
            return None

        return min(
            available_memories,
            key=lambda location:
                abs(location[0] - self.x)
                + abs(location[1] - self.y),
        )

    def _update_food_memory_cooldowns(self):
        expired = []

        for location in self.food_memory_cooldowns:
            self.food_memory_cooldowns[location] -= 1

            if self.food_memory_cooldowns[location] <= 0:
                expired.append(location)

        for location in expired:
            del self.food_memory_cooldowns[location]

    # -----------------------------------------------------------------
    # Movement and targeting
    # -----------------------------------------------------------------

    def _move_toward_target(
        self,
        world,
    ):
        if (
            self.target_x is None
            or self.target_y is None
        ):
            return

        if self._is_at_target():
            return

        if not self.path:
            self.path = world.find_path(
                self.x,
                self.y,
                self.target_x,
                self.target_y,
            )

            if not self.path:
                self.clear_target()
                return

        next_x, next_y = self.path.pop(0)

        if not self.move(
            world,
            next_x,
            next_y,
        ):
            self.path.clear()

    def _is_at_target(self):
        return (
            self.x == self.target_x
            and self.y == self.target_y
        )

    def _wander(self, world):
        directions = MOVEMENT_DIRECTIONS.copy()
        random.shuffle(directions)

        for dx, dy in directions:
            next_x = self.x + dx
            next_y = self.y + dy

            if self.move(world, next_x, next_y):
                return

    def set_target(self, world, x, y):
        self.target_x = x
        self.target_y = y

        self.path = world.find_path(
            self.x,
            self.y,
            x,
            y,
        )

    def _clear_movement_target(self):
        # Clears movement/pathing only. Use this when a social behavior
        # wants to pause walking without forgetting who it's interacting
        # with (target_monkey_id is preserved).
        self.target_x = None
        self.target_y = None
        self.path.clear()

    def clear_target(self):
        # Full disengage: clears movement AND forgets the social
        # target, so `target_monkey_id` doesn't go stale once a monkey
        # moves on to food/sleep/wander/etc.
        self._clear_movement_target()
        self.target_monkey_id = None
        self.target_tourist_id = None

    def move(self, world, x, y):
        if not world.is_walkable(x, y):
            return False

        self.x = x
        self.y = y

        self.moved_this_tick = True
        self.use_movement_energy()

        return True

    def should_follow_mother(self) -> bool:
        return (
            self.alive and self.parent_ids is not None and self.get_life_stage() in ("infant", "juvenile")
        )

    def _get_mother(self, world):
        if self.parent_ids is None:
            return None
        for parent_id in self.parent_ids:
            parent = world.get_monkey_by_id(parent_id)
            if (parent is not None and parent.alive and parent.gender == "female"):
                return parent

        return None

    def follow_mother(self, world):
        mother = self._get_mother(world)

        if mother is None:
            return False

        distance = max(
            abs(self.x - mother.x),
            abs(self.y - mother.y),
        )

        if distance <= MOTHER_FOLLOW_DISTANCE:
            return False

        self.state = FOLLOW_MOTHER_STATE
        self.set_target(world, mother.x, mother.y)
        self._move_toward_target(world)

        return True

    # -----------------------------------------------------------------
    # Energy and sleep
    # -----------------------------------------------------------------

    def update_awake_energy(self):
        self.energy = max(
            0.0,
            self.energy - IDLE_COST,
        )

    def use_movement_energy(self):
        self.energy = max(
            0.0,
            self.energy - MOVEMENT_COST,
        )

    def _handle_seeking_shelter(self, world):
        self.state = SEEKING_SHELTER_STATE

        if self.target_x is None or self.target_y is None:
            target = world.find_nearest_shelter(
                self.x,
                self.y,
            )

            if target is None:
                self._wander(world)
                return

            self.set_target(
                world,
                target.x,
                target.y,
            )

        if self._is_at_target():
            self._start_sleeping()
            return

        self._move_toward_target(world)

    def _start_sleeping(self):
        self.state = SLEEPING_STATE
        self.clear_target()

    def _sleep(self, world):
        self.energy = min(
            MAX_ENERGY,
            self.energy + SLEEP_ENERGY_RECOVERY,
        )

        if self.energy >= WAKE_ENERGY_THRESHOLD:
            self.state = WANDER_STATE

    # -----------------------------------------------------------------
    # Environmental risk
    # -----------------------------------------------------------------

    def calculate_risk(self, world):
        if self.state == SLEEPING_STATE:
            if world.is_daytime():
                return DAY_SLEEP_RISK

            return NIGHT_SLEEP_RISK

        if self.moved_this_tick:
            return MOVING_RISK

        if world.is_daytime():
            return DAY_IDLE_RISK

        return NIGHT_IDLE_RISK

    def apply_environmental_risk(self, world):
        risk = self.calculate_risk(world)

        if random.random() < risk:
            self.energy = max(
                0.0,
                self.energy - RISK_ENERGY_COST,
            )

    # -----------------------------------------------------------------
    # Health and survival
    # -----------------------------------------------------------------

    def _update_survival(self):
        if self.hunger >= MAX_HUNGER:
            self.starving_ticks += 1
        else:
            self.starving_ticks = 0

        if self.energy <= 0:
            self.exhausted_ticks += 1
        else:
            self.exhausted_ticks = 0

        if self.starving_ticks >= MAX_STARVING_TICK:
            self.take_damage(STARVATION_DAMAGE)
            # self.alive = False
            return

        if self.exhausted_ticks >= MAX_EXHAUSTED_TICK:
            self.take_damage(EXHAUST_DAMAGE)
            return

        if self.age >= MAX_AGE_DAYS:
            self.die()

    def take_damage(
        self,
        amount: float,
        apply_vulnerability: bool = True,
    ):
        if amount <= 0:
            return

        if apply_vulnerability:
            amount *= self.get_vulnerability_mod()

        self.health = max(
            0.0,
            self.health - amount,
        )

        if self.health <= 0:
            self.die()

    def heal(self, amount: float):
        if amount <= 0:
            return

        self.health = min(
            MAX_HEALTH,
            self.health + amount,
        )

    def is_dead(self):
        return self.health <= 0

    def die(self):
        self.health = 0.0
        self.alive = False
        self.clear_target()

    # -----------------------------------------------------------------
    # Life stages and maturity
    # -----------------------------------------------------------------

    def get_life_stage(self) -> str:
        if self.age < INFANT_MAX_AGE:
            return "infant"

        if self.age < JUVENILE_MAX_AGE:
            return "juvenile"

        if self.age < ELDERLY_MIN_AGE:
            return "adult"

        return "elderly"

    def get_vulnerability_mod(self) -> float:
        stage = self.get_life_stage()

        if stage == "infant":
            return 1.5

        if stage == "juvenile":
            return 1.2

        if stage == "adult":
            return 1.0

        if stage == "elderly":
            return 1.4

        return 1.0

    def get_maturity_mod(self) -> float:
        stage = self.get_life_stage()

        if stage == "infant":
            return 0.2

        if stage == "juvenile":
            return 0.6

        if stage == "adult":
            return 1.0

        if stage == "elderly":
            return 0.85

        return 1.0

    def get_effective_memory(self) -> float:
        return self.memory * self.get_maturity_mod()

    def can_reproduce(self, current_tick: int) -> bool:

        if not self.alive:
            return False
        if self.get_life_stage() != "adult":
            return False

        if self.energy < MIN_REPRODUCTION_ENERGY:
            return False

        if self.health < MIN_REPRODUCTION_HEALTH:
            return False

        if (
            self.last_reproduction_tick is not None
            and current_tick - self.last_reproduction_tick
            < REPRODUCTION_COOLDOWN_TICKS
        ):
            return False

        return True

    def is_compatible_for_reproduction(self, other: "Monkey", current_tick: int) -> bool:
        if self.id == other.id:
            return False
        if self.gender == other.gender:
            return False
        if not self.can_reproduce(current_tick) or not other.can_reproduce(current_tick):
            return False

        return True

    # -----------------------------------------------------------------
    # Monkey Behavior and Interaction
    # -----------------------------------------------------------------

    def _observe_monkeys(self, world):
        return observe_monkeys(self, world)

    def _chebyshev_distance(self, x, y):
        return max(abs(self.x - x), abs(self.y - y))

    def _choose_social_target(self, visible_monkeys, current_tick):
        return choose_social_target(self, visible_monkeys, current_tick)

    def _desired_social_distance(self, other):
        return desired_social_distance(self, other)

    def _handle_social_interaction(self, world, visible_monkeys):
        return handle_social_interaction(self, world, visible_monkeys)

    def _step_away_from(self, world, other):
        step_away_from(self, world, other)

    def _flee_from(self, world, other):
        flee_from(self, world, other)

    def _confront(self, world, other):
        confront(self, world, other)

    # -----------------------------------------------------------------
    # Monkey Behavior and Interaction
    # -----------------------------------------------------------------

    def _observe_tourists(self, world):
        return observe_tourists(self, world)

    def _choose_tourist_to_investigate(self, world):
        return choose_tourist_to_investigate(self, world)

    def _handle_tourist_investigation(
        self,
        world,
        visible_tourists,
    ):
        return handle_tourist_investigation(self, world, visible_tourists)

    def _handle_tourist_interactions(self, world, tourist):
        return handle_tourist_interactions(self, world, tourist)

    def _update_tourist_interaction_ticks(self):
       return update_tourist_interaction_ticks(self)

    def _update_tourist_interaction_cooldown(self):
       return update_tourist_interaction_cooldown(self)


    def grab_item(self, world, tourist, item):
        return grab_item_monkey(self, world, tourist, item)


    def _choose_tourist_action(self, tourist):
        return choose_tourist_action(tourist)

    def _execute_tourist_action(self, world, tourist, action):
        return execute_tourist_action(self, world, tourist, action)


    def _get_tourist_state(self, tourist):
        return get_tourist_state(self, tourist)
    
    def _get_valid_actions(self, world):
        return get_valid_actions(self, world)

    # -----------------------------------------------------------------
    # Reward Pathways
    # -----------------------------------------------------------------
    
    def _calculate_reward(self, previous_health, previous_energy, previous_hunger):
        return calculate_reward(self, previous_health, previous_energy, previous_hunger)

    def _encode_tourist_action(self, action):
        return encode_tourist_action(action)
    
    def _encode_monkey_action(self, action):
        return encode_monkey_action(action)

    def _finalize_tourist_experience(self, world):
        return finalize_tourist_experience(self, world)

    def _get_brain_state(self, world):
        return get_brain_state(self,world)

    def _get_brain_output(self, world):
        return get_brain_output(self,world)

    def _choose_brain_action(self, state, world):
        return choose_brain_action(self,state,world)

    def _finalize_brain_experience(self, world):
        return finalize_brain_experience(
            self,
            world,
        )

    def _train_brain(self):
        return train_brain(self)
    # -----------------------------------------------------------------
    # API representation
    # -----------------------------------------------------------------

    def to_dict(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "hunger": round(self.hunger, 1),
            "age": self.age,
            "life_stage": self.get_life_stage(),
            "health": round(self.health, 1),
            "name": self.name,
            "energy": round(self.energy, 1),
            "tourist_interaction_ticks": self.tourist_interaction_ticks,
            "state": self.state,
            "target_monkey_id": self.target_monkey_id,
            "gender": self.gender,
            "traits": {
                "boldness": round(self.boldness, 2),
                "curiosity": round(self.curiosity, 2),
                "sociability": round(self.sociability, 2),
                "memory": round(self.memory, 2),
                "aggression": round(self.aggression, 2),
                "effective_memory": round(
                    self.get_effective_memory(),
                    2,
                ),
            },
            "target": {
                "x": self.target_x,
                "y": self.target_y,
            }
            if self.target_x is not None
            and self.target_y is not None
            else None,
            "food_memory": [
                {
                    "x": x,
                    "y": y,
                }
                for x, y in self.food_memory
            ],
            "current_tourist_action": self.current_tourist_action,
            "last_tourist_action": self.last_tourist_action,
            "last_tourist_action_success": self.last_tourist_action_success,
            "held_items": [
                {
                    "name": item.name,
                    "value": item.value,
                }
                for item in self.held_items
            ],
            "reward": round(self.reward, 2),

            "brain_experience_count": len(
                self.brain_experiences
            ),

            "training_loss": (
                round(self.last_training_loss, 4)
                if self.last_training_loss is not None
                else None
            ),
        }
