from dataclasses import dataclass
import random


WANDER_STATE = "wandering"
SEEKING_FOOD_STATE = "seeking_food"
EATING_STATE = "eating"

HUNGER_PER_TICK = 0.5
FOOD_SEEK_THRESHOLD = 60.0
MAX_HUNGER = 100.0

FRUIT_HUNGER_REDUCTION = 25.0

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
    hunger: float = 0.0
    state: str = WANDER_STATE
    target_x: int | None = None
    target_y: int | None = None

    def update(self, world):
        self._increase_hunger()

        if self.hunger >= FOOD_SEEK_THRESHOLD:
            self._handle_food_seeking(world)
            return

        self.state = WANDER_STATE
        self.clear_target()
        self._wander(world)

    def _increase_hunger(self):
        self.hunger = min(
            MAX_HUNGER,
            self.hunger + HUNGER_PER_TICK,
        )

    def _handle_food_seeking(self, world):
        self.state = SEEKING_FOOD_STATE

        if self.target_x is None or self.target_y is None:
            target = world.find_nearest_fruit_tree(
                self.x,
                self.y,
            )

            if target is None:
                self._wander(world)
                return

            self.set_target(
                target.x,
                target.y,
            )

        if self._is_at_target():
            self._eat_from_target(world)
            return

        self._move_toward_target(world)

    def _eat_from_target(self, world):
        if self.target_x is None or self.target_y is None:
            return

        self.state = EATING_STATE

        harvested = world.harvest_tree_fruit(
            self.target_x,
            self.target_y,
            1,
        )

        if harvested <= 0:
            self.clear_target()
            self.state = SEEKING_FOOD_STATE
            return

        self.eat(
            harvested * FRUIT_HUNGER_REDUCTION,
        )

    def _move_toward_target(self, world):
        if self.target_x is None or self.target_y is None:
            return

        dx = self._direction_to(
            self.target_x - self.x,
        )

        dy = self._direction_to(
            self.target_y - self.y,
        )

        preferred_moves = [
            (dx, dy),
            (dx, 0),
            (0, dy),
        ]

        for move_x, move_y in preferred_moves:
            if move_x == 0 and move_y == 0:
                continue

            next_x = self.x + move_x
            next_y = self.y + move_y

            if not self._can_move_to(
                world,
                next_x,
                next_y,
            ):
                continue

            self.x = next_x
            self.y = next_y
            return

        self._wander(world)

    def _direction_to(self, difference):
        if difference > 0:
            return 1

        if difference < 0:
            return -1

        return 0

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

            if not self._can_move_to(
                world,
                next_x,
                next_y,
            ):
                continue

            self.x = next_x
            self.y = next_y
            return

    def _can_move_to(self, world, x, y):
        tile = world.get_tile(x, y)

        if tile is None:
            return False

        blocked_terrain = {
            "water",
            "mountain",
            "snow",
        }

        return tile.terrain not in blocked_terrain

    def set_target(self, x, y):
        self.target_x = x
        self.target_y = y

    def clear_target(self):
        self.target_x = None
        self.target_y = None

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
            "state": self.state,
            "target": {
                "x": self.target_x,
                "y": self.target_y,
            }
            if self.target_x is not None
            and self.target_y is not None
            else None,
        }

 