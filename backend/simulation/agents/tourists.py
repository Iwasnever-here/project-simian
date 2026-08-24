from dataclasses import dataclass, field
import random
from .touristItem import TouristItem


HEADING_TO_TEMPLE = "heading_to_temple"
WANDERING_TEMPLE = "wandering_temple"
INSIDE_TEMPLE = "inside_temple"
HEADING_TO_BOAT = "heading_to_boat"


TEMPLE_WANDER_RADIUS = 8

MIN_TEMPLE_STAY_MINUTES = 10
MAX_TEMPLE_STAY_MINUTES = 60

TEMPLE_ENTRY_CHANCE = 0.5

# If find_path fails (no route to target), wait this many ticks before
# retrying instead of re-running A* over the whole map every single tick.
PATH_RETRY_COOLDOWN_TICKS = 20


@dataclass
class Tourist:
    id: int
    name: str
    value: float

    x: int
    y: int

    temple_x: int
    temple_y: int

    boat_x: int
    boat_y: int

    state: str = HEADING_TO_TEMPLE

    path: list[tuple[int, int]] = field(
        default_factory=list
    )

    wander_target: tuple[int, int] | None = None

    inside_temple: bool = False

    temple_entry_tick: int | None = None
    temple_exit_tick: int | None = None

    path_retry_cooldown: int = 0

    # Ticks to wait after spawning before starting to move — staggers
    # a boatload of tourists so they don't walk in perfect lockstep.
    spawn_delay: int = 0

    alive: bool = True

    items: list[TouristItem] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "x": self.x,
            "y": self.y,
            "alive": self.alive,
            "items": [{"name": i.name, "value": i.value} for i in self.items],
        }
    
    def update(
        self,
        world,
        current_hour: float,
        current_tick: int,
    ):
        if not self.alive:
            return

        if self.spawn_delay > 0:
            self.spawn_delay -= 1
            return

        if current_hour >= 17:
            self.start_returning_to_boat(world)

        if self.state == HEADING_TO_TEMPLE:
            self.head_to_temple(world)

        elif self.state == WANDERING_TEMPLE:
            self.wander_near_temple(world)

        elif self.state == INSIDE_TEMPLE:
            self.update_inside_temple(
                world,
                current_tick,
            )

        elif self.state == HEADING_TO_BOAT:
            self.head_to_boat(world)

    def _seek_path(self, world, target):
        """Try to (re)build a path to target, throttling retries after a
        failed search so a stuck tourist doesn't re-run A* every tick."""
        if self.path:
            return

        if self.path_retry_cooldown > 0:
            self.path_retry_cooldown -= 1
            return

        self.path = world.find_path(
            self.x,
            self.y,
            target[0],
            target[1],
        )

        if not self.path:
            self.path_retry_cooldown = PATH_RETRY_COOLDOWN_TICKS

    def head_to_temple(self, world):
        target = (self.temple_x, self.temple_y)

        if self.has_reached(target):
            self.path.clear()
            self.path_retry_cooldown = 0

            self.choose_temple_activity(world)
            return

        self._seek_path(world, target)
        self.follow_path()

    def choose_temple_activity(self, world):
        wants_to_enter = (random.random() < TEMPLE_ENTRY_CHANCE)

        if wants_to_enter:
            entered = world.try_enter_temple(self)

            if entered:
                return

        self.start_wandering_near_temple()

    def enter_temple(self, current_tick: int, ticks_per_hour: int,):
        self.inside_temple = True
        self.state = INSIDE_TEMPLE

        self.path.clear()
        self.path_retry_cooldown = 0
        self.wander_target = None

        self.temple_entry_tick = current_tick

        min_stay_ticks = max(
            1,
            int(ticks_per_hour * (MIN_TEMPLE_STAY_MINUTES / 60)),
        )

        max_stay_ticks = max(
            min_stay_ticks,
            int(ticks_per_hour * (MAX_TEMPLE_STAY_MINUTES / 60)),
        )

        stay_ticks = random.randint(
            min_stay_ticks,
            max_stay_ticks,
        )

        self.temple_exit_tick = (
            current_tick
            + stay_ticks
        )

    def update_inside_temple(
        self,
        world,
        current_tick: int,
    ):
        if self.temple_exit_tick is None:
            world.leave_temple(self)

            self.exit_temple()
            return

        if current_tick < self.temple_exit_tick:
            return

        world.leave_temple(self)

        self.exit_temple()

    def exit_temple(self):
        self.inside_temple = False

        self.temple_entry_tick = None
        self.temple_exit_tick = None

        self.state = WANDERING_TEMPLE

        self.path.clear()
        self.path_retry_cooldown = 0
        self.wander_target = None

    def start_wandering_near_temple(self):
        self.state = WANDERING_TEMPLE

        self.path.clear()
        self.path_retry_cooldown = 0
        self.wander_target = None

    def wander_near_temple(self, world):
        if self.wander_target is None:
            self.wander_target = (
                world.get_random_walkable_tile_near(
                    self.temple_x,
                    self.temple_y,
                    TEMPLE_WANDER_RADIUS,
                )
            )

            if self.wander_target is None:
                return

        if self.has_reached(self.wander_target):
            self.path.clear()
            self.path_retry_cooldown = 0
            self.wander_target = None

            self.choose_temple_activity(world)
            return

        self._seek_path(world, self.wander_target)

        if not self.path:
            return

        self.follow_path()

    def start_returning_to_boat(self, world,):
        if self.state == HEADING_TO_BOAT:
            return

        if self.inside_temple:
            world.leave_temple(self)

        self.inside_temple = False

        self.temple_entry_tick = None
        self.temple_exit_tick = None

        self.wander_target = None
        self.path.clear()
        self.path_retry_cooldown = 0

        self.state = HEADING_TO_BOAT

    def head_to_boat(self, world):
        target = (self.boat_x, self.boat_y)

        if self.has_reached(target):
            self.despawn()
            return

        self._seek_path(world, target)

        if not self.path:
            return

        self.follow_path()

    def follow_path(self):
        if not self.path:
            return

        next_x, next_y = self.path.pop(0)

        self.x = next_x
        self.y = next_y

    def has_reached(self, target: tuple[int, int],) -> bool:
        target_x, target_y = target

        return (self.x == target_x and self.y == target_y)

    def despawn(self):
        self.alive = False

        self.path.clear()
        self.path_retry_cooldown = 0
        self.wander_target = None

        self.inside_temple = False
        self.temple_entry_tick = None
        self.temple_exit_tick = None