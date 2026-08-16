from dataclasses import dataclass, field
import random




WANDER_STATE = "wandering"
SEEKING_FOOD_STATE = "seeking_food"
EATING_STATE = "eating"
SLEEPING_STATE = "sleeping"
SEEKING_SHELTER_STATE = "seeking_shelter"

HUNGER_PER_TICK = 0.5
FOOD_SEEK_THRESHOLD = 60.0
MAX_HUNGER = 100.0

FRUIT_HUNGER_REDUCTION = 25.0


SLEEP_ENERGY_THRESHOLD = 30.0
WAKE_ENERGY_THRESHOLD = 80.0
MAX_ENERGY = 100.0

MAX_STARVING_TICK = 20
MAX_EXHAUSTED_TICK = 20
MAX_AGE_DAYS = 3650

SLEEP_ENERGY_RECOVERY = 1.0

VISION_RANGE = 5
MAX_FOOD_MEMORIES = 4
FOOD_MEMORY_COOLDOWN_TICKS = 20

MOVEMENT_COST = 0.25
IDLE_COST = 0.05
DAY_SLEEP_RISK = 0.005
NIGHT_SLEEP_RISK = 0.0005
DAY_IDLE_RISK = 0.001
NIGHT_IDLE_RISK = 0.0005
MOVING_RISK = 0.0003
RISK_ENERGY_COST = 5.0



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


@dataclass
class Monkey:
    id: int
    x: int
    y: int
    gender: str
    name: str
    hunger: float = 0.0
    age: int = 0
    energy: float = 100.0
    state: str = WANDER_STATE
    target_x: int | None = None
    target_y: int | None = None
    starving_ticks: int = 0
    exhausted_ticks: int = 0
    alive: bool = True
    food_memory: list[tuple[int, int]] = field(default_factory=list)
    food_memory_cooldowns: dict[tuple[int, int], int] = field(default_factory=dict)
    path: list[tuple[int, int]] = field(default_factory=list)
    moved_this_tick: bool = False


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

            # Food currently has higher priority than sleep.
            if self.hunger >= FOOD_SEEK_THRESHOLD:
                self._handle_food_seeking(world)

            # Low energy means find somewhere to sleep.
            elif (
                self.energy <= SLEEP_ENERGY_THRESHOLD
                or self.state == SEEKING_SHELTER_STATE
            ):
                self._handle_seeking_shelter(world)

            else:
                self.state = WANDER_STATE
                self.clear_target()
                self._wander(world)

        self.apply_environmental_risk(world)
        self._update_survival()

    def update_awake_energy(self):
        self.energy = max(
            0.0,
            self.energy - IDLE_COST
        )

    def _update_food_memory_cooldowns(self):
        expired = []

        for location in self.food_memory_cooldowns:
            self.food_memory_cooldowns[location] -= 1

            if self.food_memory_cooldowns[location] <= 0:
                expired.append(location)

        for location in expired:
            del self.food_memory_cooldowns[location]

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
                remembered_location = (
                    self._find_remembered_food()
                )

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

    def clear_target(self):
        self.target_x = None
        self.target_y = None
        self.path.clear()

    def eat(self, food_amount):
        if food_amount <= 0:
            return

        self.hunger = max(
            0.0,
            self.hunger - food_amount,
        )

        self.state = WANDER_STATE
        self.clear_target()

    def to_dict(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "hunger": round(self.hunger, 1),
            "age": self.age,
            "name": self.name,
            "energy": round(self.energy, 1),
            "state": self.state,
            "gender": self.gender,
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
            self.alive = False
            return

        if self.exhausted_ticks >= MAX_EXHAUSTED_TICK:
            self.alive = False
            return

        if self.age >= MAX_AGE_DAYS:
            self.alive = False

    def _find_visible_food(self, world):
        print(
            f"\nMonkey {self.id}: "
            f"pos=({self.x}, {self.y}), "
            f"hunger={self.hunger}"
        )

        current_tree = world.get_tree(
            self.x,
            self.y,
        )

        if current_tree:
            print(
                "TREE UNDER MONKEY:",
                current_tree.species,
                "fruit:",
                current_tree.fruit,
            )
        else:
            print("NO TREE UNDER MONKEY")

        nearby_trees = []

        for tree in world.trees.values():
            distance = max(
                abs(tree.x - self.x),
                abs(tree.y - self.y),
            )

            if distance <= VISION_RANGE:
                nearby_trees.append(tree)

        print(
            "ALL NEARBY TREES:",
            [
                (
                    tree.x,
                    tree.y,
                    tree.species,
                    tree.fruit,
                )
                for tree in nearby_trees
            ],
        )

        trees = world.get_visible_fruit_trees(
            self.x,
            self.y,
            VISION_RANGE,
        )

        print(
            f"VISIBLE FOOD: {len(trees)}"
        )

        if not trees:
            return None

        return min(
            trees,
            key=lambda tree:
                abs(tree.x - self.x)
                + abs(tree.y - self.y),
        )

    def use_movement_energy(self):
        self.energy = max(
            0.0,
            self.energy - MOVEMENT_COST,
        )

    def move(self, world, x, y):
        if not world.is_walkable(x, y):
            return False

        self.x = x
        self.y = y

        self.moved_this_tick = True
        self.use_movement_energy()

        return True

    def calculate_risk(self, world):
        if self.state == SLEEPING_STATE:
            if world.is_daytime:
                return DAY_SLEEP_RISK

            return NIGHT_SLEEP_RISK

        if self.moved_this_tick:
            return MOVING_RISK

        if world.is_daytime:
            return DAY_IDLE_RISK

        return NIGHT_IDLE_RISK   

    def apply_environmental_risk(self, world):
        risk = self.calculate_risk(world)

        if random.random() < risk:
            self.energy = max(
                0.0,
                self.energy - RISK_ENERGY_COST 
            )

    