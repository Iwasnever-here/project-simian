from dataclasses import dataclass, field
import random

from backend.simulation.agents.monkeyMemory import MonkeyMemory


# ---------------------------------------------------------------------
# Monkey states
# ---------------------------------------------------------------------

WANDER_STATE = "wandering"
SEEKING_FOOD_STATE = "seeking_food"
EATING_STATE = "eating"
SLEEPING_STATE = "sleeping"
SEEKING_SHELTER_STATE = "seeking_shelter"
FOLLOW_MOTHER_STATE = "following_mother"
APPROACHING_MONEKY_STATE = "approaching_monkey"
AVOIDING_MONKEY_STATE = "avoiding_monkey"
FOLLOWING_MONKEY_STATE = "following_monkey"
CONFRONTING_MONKEY_STATE = "confronting_monkey"
SOCIAL_IDLE_STATE = "socializing"


# ---------------------------------------------------------------------
# Hunger and food
# ---------------------------------------------------------------------

HUNGER_PER_TICK = 0.5
FOOD_SEEK_THRESHOLD = 60.0
MAX_HUNGER = 100.0

FRUIT_HUNGER_REDUCTION = 25.0

MAX_FOOD_MEMORIES = 4
FOOD_MEMORY_COOLDOWN_TICKS = 20


# ---------------------------------------------------------------------
# Energy and sleep
# ---------------------------------------------------------------------

SLEEP_ENERGY_THRESHOLD = 30.0
WAKE_ENERGY_THRESHOLD = 80.0
MAX_ENERGY = 100.0
SLEEP_ENERGY_RECOVERY = 1.0

MOVEMENT_COST = 0.25
IDLE_COST = 0.05


# ---------------------------------------------------------------------
# Survival and risk
# ---------------------------------------------------------------------

MAX_STARVING_TICK = 10
MAX_EXHAUSTED_TICK = 10
MAX_AGE_DAYS = 3650

DAY_SLEEP_RISK = 0.005
NIGHT_SLEEP_RISK = 0.0005
DAY_IDLE_RISK = 0.001
NIGHT_IDLE_RISK = 0.0005
MOVING_RISK = 0.0003
RISK_ENERGY_COST = 5.0

MAX_HEALTH = 100.0
STARVATION_DAMAGE = 2.0
EXHAUST_DAMAGE = 1.0


# ---------------------------------------------------------------------
# Life stages
# ---------------------------------------------------------------------

INFANT_MAX_AGE = 50
JUVENILE_MAX_AGE = 100
ELDERLY_MIN_AGE = 300

MIN_REPRODUCTION_ENERGY = 50.0
MIN_REPRODUCTION_HEALTH = 50.0
REPRODUCTION_COOLDOWN_TICKS = 1000
REPRODUCTION_ENERGY_COST = 20.0
REPRODUCTION_RANGE = 1
TRAIT_MUTATION_STDDEV = 0.05


# ---------------------------------------------------------------------
# Traits
# ---------------------------------------------------------------------

MIN_TRAIT_VALUE = 0.0
MAX_TRAIT_VALUE = 1.0


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

VISION_RANGE = 5

MOVEMENT_DIRECTIONS = [
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
    (1, 1),
    (1, -1),
    (-1, 1),
    (-1, -1),
]

MOTHER_FOLLOW_DISTANCE = 2

# Social spacing: instead of fixed "approach vs avoid" cutoffs, monkeys
# converge on a desired distance derived from sociability/aggression,
# with a hysteresis band so they settle instead of oscillating.
MIN_SOCIAL_DISTANCE = 1
MAX_SOCIAL_DISTANCE = 4
SOCIAL_DISTANCE_HYSTERESIS = 1
SOCIAL_DECISION_TICKS = 15
SOCIAL_MEMORY_RECENCY_TICKS = 300
AGGRESSION_DOMINANCE_THRESHOLD = 0.2


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

    # Memory and pathfinding
    food_memory: list[tuple[int, int]] = field(default_factory=list)
    food_memory_cooldowns: dict[tuple[int, int], int] = field(
        default_factory=dict
    )
    path: list[tuple[int, int]] = field(default_factory=list)

    social_memory: MonkeyMemory = field(default_factory=MonkeyMemory)

    # Per-tick movement state
    moved_this_tick: bool = False

    # -----------------------------------------------------------------
    # Main update
    # -----------------------------------------------------------------

    def update(self, world):
        if not self.alive:
            return

        self.moved_this_tick = False

        self._increase_hunger()
        self._update_food_memory_cooldowns()

        if self.state == SLEEPING_STATE:
            self._sleep(world)

        else:
            self.update_awake_energy()

            visible_monkeys = self._observe_monkeys(world)

            # Food currently has higher priority than sleep.
            if self.hunger >= FOOD_SEEK_THRESHOLD:
                self._handle_food_seeking(world)

            # Low energy means find somewhere to sleep.
            elif (
                self.energy <= SLEEP_ENERGY_THRESHOLD
                or self.state == SEEKING_SHELTER_STATE
            ):
                self._handle_seeking_shelter(world)
            elif (
                self.should_follow_mother()
                and self.follow_mother(world)
            ):
                pass
            elif self._handle_social_interaction(
                world,
                visible_monkeys,
            ):
                pass

            else:
                self.state = WANDER_STATE
                self.clear_target()
                self._wander(world)

        self.apply_environmental_risk(world)
        self._update_survival()

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
        visible_monkeys = world.get_visible_monkeys(
            self.id,
            self.x,
            self.y,
            VISION_RANGE,
        )
        for other in visible_monkeys:
            self.social_memory.remember(
                other.id,
                other.x,
                other.y,
                world.total_tick,
            )
        return visible_monkeys

    def _chebyshev_distance(self, x, y):
        return max(abs(self.x - x), abs(self.y - y))

    def _choose_social_target(self, visible_monkeys, current_tick):
        # Prefer someone this monkey actually recognizes over a random
        # stranger, so the `memory` trait has a real effect on who
        # gets interacted with.
        known_recent = [
            m for m in visible_monkeys
            if (record := self.social_memory.get(m.id)) is not None
            and current_tick - record.last_seen_tick <= SOCIAL_MEMORY_RECENCY_TICKS
        ]

        candidates = known_recent if known_recent else visible_monkeys

        return min(
            candidates,
            key=lambda m: self._chebyshev_distance(m.x, m.y),
        )

    def _desired_social_distance(self, other):
        base = MIN_SOCIAL_DISTANCE + (
            1.0 - self.sociability
        ) * (
            MAX_SOCIAL_DISTANCE
            - MIN_SOCIAL_DISTANCE
        )

        threat = other.aggression
        confidence = self.aggression

        base += threat * 1.5
        base -= confidence * 1.5

        return max(
            MIN_SOCIAL_DISTANCE,
            min(MAX_SOCIAL_DISTANCE, base),
        )

    def _handle_social_interaction(self, world, visible_monkeys):
        if not visible_monkeys:
            return False

        other = self._choose_social_target(visible_monkeys, world.total_tick)
        distance = self._chebyshev_distance(other.x, other.y)

        aggression_gap = other.aggression - self.aggression

        # Fear overrides sociability: a much less aggressive monkey
        # flees a much more aggressive one on sight.
        if aggression_gap >= AGGRESSION_DOMINANCE_THRESHOLD:
            self._flee_from(world, other)
            return True

        # Dominance: a much more aggressive monkey closes in to
        # intimidate, regardless of how sociable it is.
        if -aggression_gap >= AGGRESSION_DOMINANCE_THRESHOLD:
            self._confront(world, other)
            return True

        # Otherwise, converge on a comfortable equilibrium distance
        # rather than re-deciding a fresh behavior every single tick.
        same_target = self.target_monkey_id == other.id

        if same_target and self.social_decision_cooldown > 0:
            self.social_decision_cooldown -= 1
        else:
            self.target_monkey_id = other.id
            self.social_decision_cooldown = SOCIAL_DECISION_TICKS

        desired = self._desired_social_distance(other)

        if distance > desired + SOCIAL_DISTANCE_HYSTERESIS:
            self.state = (
                APPROACHING_MONEKY_STATE
                if self.sociability >= 0.7
                else FOLLOWING_MONKEY_STATE
            )
            self._clear_movement_target()
            self.set_target(world, other.x, other.y)
            self._move_toward_target(world)

        elif distance < desired - SOCIAL_DISTANCE_HYSTERESIS:
            self._flee_from(world, other)

        else:
            self.state = SOCIAL_IDLE_STATE
            self._clear_movement_target()

        return True

    def _step_away_from(self, world, other):
        dx = self.x - other.x
        dy = self.y - other.y

        step_x = (dx > 0) - (dx < 0)
        step_y = (dy > 0) - (dy < 0)

        if self.move(world, self.x + step_x, self.y + step_y):
            return

        self._wander(world)

    def _flee_from(self, world, other):
        self.state = AVOIDING_MONKEY_STATE
        self.target_monkey_id = other.id
        self._clear_movement_target()

        self._step_away_from(world, other)

    def _confront(self, world, other):
        self.state = CONFRONTING_MONKEY_STATE
        self.target_monkey_id = other.id

        if self._chebyshev_distance(other.x, other.y) <= MIN_SOCIAL_DISTANCE:
            self._clear_movement_target()
            return

        self._clear_movement_target()
        self.set_target(world, other.x, other.y)
        self._move_toward_target(world)

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
        }
