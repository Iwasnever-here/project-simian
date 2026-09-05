from dataclasses import dataclass, field
import random

from .touristItem import TouristItem


HEADING_TO_TEMPLE = "heading_to_temple"
WANDERING_TEMPLE = "wandering_temple"
INSIDE_TEMPLE = "inside_temple"
HEADING_TO_BOAT = "heading_to_boat"
FLEEING_MONKEY = "fleeing_monkey"

TEMPLE_WANDER_RADIUS = 8
MIN_TEMPLE_STAY_MINUTES = 10
MAX_TEMPLE_STAY_MINUTES = 60
TEMPLE_ENTRY_CHANCE = 0.5

# If find_path fails, wait this many ticks before retrying instead of
# re-running A* over the whole map every single tick.
PATH_RETRY_COOLDOWN_TICKS = 20

FLEE_SAFE_DISTANCE = 6
TOURIST_MONKEY_VISION_RANGE = 5


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
    path: list[tuple[int, int]] = field(default_factory=list)
    wander_target: tuple[int, int] | None = None

    inside_temple: bool = False
    temple_entry_tick: int | None = None
    temple_exit_tick: int | None = None

    path_retry_cooldown: int = 0

    # Staggers a boatload of tourists so they do not move in lockstep.
    spawn_delay: int = 0

    alive: bool = True
    threat_monkey_id: int | None = None
    items: list[TouristItem] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "x": self.x,
            "y": self.y,
            "alive": self.alive,
            "state": self.state,
            "threat_monkey_id": self.threat_monkey_id,
            "items": [{"name": item.name, "value": item.value} for item in self.items],
        }

    # -----------------------------------------------------------------
    # Main update
    # -----------------------------------------------------------------

    def update(self, world, current_hour: float, current_tick: int):
        if not self.alive:
            return

        if self.spawn_delay > 0:
            self.spawn_delay -= 1
            return

        # Returning to the boat takes priority over monkey interactions.
        if current_hour >= 17:
            self.start_returning_to_boat(world)
        else:
            threat = self._find_threatening_monkey(world)

            if threat is not None:
                if self.threat_monkey_id != threat.id:
                    self.path.clear()
                    self.path_retry_cooldown = 0
                    self.wander_target = None

                self.threat_monkey_id = threat.id
                self.state = FLEEING_MONKEY

        if self.state == HEADING_TO_TEMPLE:
            self.head_to_temple(world)

        elif self.state == WANDERING_TEMPLE:
            self.wander_near_temple(world)

        elif self.state == INSIDE_TEMPLE:
            self.update_inside_temple(world, current_tick)

        elif self.state == HEADING_TO_BOAT:
            self.head_to_boat(world)

        elif self.state == FLEEING_MONKEY:
            self._flee_from_monkey(world)

    # -----------------------------------------------------------------
    # Pathfinding
    # -----------------------------------------------------------------

    def _seek_path(self, world, target):
        if self.path:
            return

        if self.path_retry_cooldown > 0:
            self.path_retry_cooldown -= 1
            return

        self.path = world.find_path(self.x, self.y, target[0], target[1])

        if not self.path:
            self.path_retry_cooldown = PATH_RETRY_COOLDOWN_TICKS

    def follow_path(self):
        if not self.path:
            return

        self.x, self.y = self.path.pop(0)

    def has_reached(self, target: tuple[int, int]) -> bool:
        target_x, target_y = target
        return self.x == target_x and self.y == target_y

    # -----------------------------------------------------------------
    # Temple behaviour
    # -----------------------------------------------------------------

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
        if random.random() < TEMPLE_ENTRY_CHANCE:
            if world.try_enter_temple(self):
                return

        self.start_wandering_near_temple()

    def enter_temple(self, current_tick: int, ticks_per_hour: int):
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

        stay_ticks = random.randint(min_stay_ticks, max_stay_ticks)
        self.temple_exit_tick = current_tick + stay_ticks

    def update_inside_temple(self, world, current_tick: int):
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
            self.wander_target = world.get_random_walkable_tile_near(
                self.temple_x,
                self.temple_y,
                TEMPLE_WANDER_RADIUS,
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

    # -----------------------------------------------------------------
    # Boat behaviour
    # -----------------------------------------------------------------

    def start_returning_to_boat(self, world):
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
        self.threat_monkey_id = None
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

    def despawn(self):
        self.alive = False
        self.path.clear()
        self.path_retry_cooldown = 0
        self.wander_target = None
        self.inside_temple = False
        self.temple_entry_tick = None
        self.temple_exit_tick = None
        self.threat_monkey_id = None

    # -----------------------------------------------------------------
    # Monkey threat behaviour
    # -----------------------------------------------------------------

    def _find_threatening_monkey(self, world):
        monkeys = world.get_nearby_monkeys(
            self.x,
            self.y,
            vision_range=TOURIST_MONKEY_VISION_RANGE,
        )

        for monkey in monkeys:
            if (
                monkey.state == "scaring_tourist"
                and monkey.target_tourist_id == self.id
            ):
                return monkey

        return None

    def _flee_from_monkey(self, world):
        if self.threat_monkey_id is None:
            self._stop_fleeing()
            return

        threat = world.get_monkey_by_id(self.threat_monkey_id)

        if threat is None:
            self._stop_fleeing()
            return

        distance_to_threat = max(
            abs(self.x - threat.x),
            abs(self.y - threat.y),
        )

        if distance_to_threat >= FLEE_SAFE_DISTANCE:
            self._stop_fleeing()
            return

        step_x = (self.x > threat.x) - (self.x < threat.x)
        step_y = (self.y > threat.y) - (self.y < threat.y)

        next_x = self.x + step_x
        next_y = self.y + step_y

        if world.is_walkable(next_x, next_y):
            self.x = next_x
            self.y = next_y

    def _stop_fleeing(self):
        self.threat_monkey_id = None
        self.path.clear()
        self.path_retry_cooldown = 0
        self.wander_target = None
        self.state = WANDERING_TEMPLE