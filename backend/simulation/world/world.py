import heapq
import random
import threading

import opensimplex

from backend.simulation.agents import tourists
from backend.simulation.agents.monkey import REPRODUCTION_RANGE
from backend.simulation.agents.monkey import MAX_HEALTH, Monkey, random_trait
from backend.simulation.agents.touristItem import generate_tourist_items
from backend.simulation.names import generate_monkey_identity
from backend.simulation.world.tile import Tile
from backend.simulation.world.tree import Tree
from backend.simulation.agents.monkey import inherit_trait
from backend.simulation.agents.monkey import REPRODUCTION_ENERGY_COST, Monkey, random_trait
from backend.simulation.names import generate_monkey_identity
from backend.simulation.world.tile import Tile
from backend.simulation.world.tree import Tree
from backend.simulation.agents.tourists import Tourist


# ---------------------------------------------------------------------
# Chunk settings
# ---------------------------------------------------------------------

CHUNK_SIZE = 32

# Single-character terrain codes keep chunk payloads compact.
TERRAIN_CODE = {
    "water": "w",
    "sand": "s",
    "grass": "g",
    "forest": "f",
    "wetland": "m",
    "mountain": "r",
    "snow": "n",
}


# ---------------------------------------------------------------------
# Temple settings
# ---------------------------------------------------------------------

TEMPLE_X = 235
TEMPLE_Y = 135
TEMPLE_WIDTH = 12
TEMPLE_HEIGHT = 10


# ---------------------------------------------------------------------
# Island shape
# ---------------------------------------------------------------------

EDGE_FALLOFF_WIDTH = 0.15
EDGE_FALLOFF_STRENGTH = 1.4


# ---------------------------------------------------------------------
# Elevation bands
# ---------------------------------------------------------------------

WATER_LEVEL = -0.2
SAND_LEVEL = -0.1
MOUNTAIN_LEVEL = 0.35
SNOW_LEVEL = 0.55


# ---------------------------------------------------------------------
# Moisture bands
# ---------------------------------------------------------------------

WETLAND_MOISTURE = 0.3
FOREST_MOISTURE = 0.0


# ---------------------------------------------------------------------
# Fractal noise settings
# ---------------------------------------------------------------------

ELEVATION_OCTAVES = 5
ELEVATION_BASE_SCALE = 0.015
ELEVATION_PERSISTENCE = 0.5
ELEVATION_LACUNARITY = 2.0

MOISTURE_OCTAVES = 4
MOISTURE_BASE_SCALE = 0.02
MOISTURE_PERSISTENCE = 0.5
MOISTURE_LACUNARITY = 2.0


# ---------------------------------------------------------------------
# Tree generation
# ---------------------------------------------------------------------

TREE_SCALE = 0.15
TREE_SPECIES_SCALE = 0.05

FOREST_TREE_THRESHOLD = 0.2
GRASS_TREE_THRESHOLD = 0.6
FRUIT_TREE_THRESHOLD = 0.00


# ---------------------------------------------------------------------
# Monkey spawning
# ---------------------------------------------------------------------

SPAWNABLE_TERRAIN_BLOCKLIST = {"water", "mountain", "snow"}
SPAWN_MAX_ATTEMPTS = 200


# ---------------------------------------------------------------------
# Tourist spawning
# ---------------------------------------------------------------------
TOURIST_ARRIVAL_HOUR = 8
TOURIST_DEPARTURE_HOUR = 17
TOURISTS_PER_DAY = 20
MAX_TEMPLE_CAPACITY = 10


# ---------------------------------------------------------------------
# World time settings
# ---------------------------------------------------------------------

TICKS_PER_DAY = 120
DAY_START = 30
NIGHT_START = 90



class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.chunk_size = CHUNK_SIZE

        # Guards shared mutable simulation state against concurrent
        # access from the simulation loop and FastAPI request threads.
        # RLock is required because locked methods can call other
        # locked methods from the same thread.
        self.lock = threading.RLock()

        # Noise generators
        self.elevation_noise = opensimplex.OpenSimplex(seed=12345)
        self.moisture_noise = opensimplex.OpenSimplex(seed=98765)
        self.tree_noise = opensimplex.OpenSimplex(seed=54321)
        self.tree_species_noise = opensimplex.OpenSimplex(seed=13579)

        # Tree state
        self.trees: dict[tuple[int, int], Tree] = {}
        self.generated_tree_chunks: set[tuple[int, int]] = set()

        # Terrain state
        self.grid = [[None] * height for _ in range(width)]

        # World time
        self.tick = 0
        self.day = 0
        self.total_tick = 0

        # Monkey state

        self.monkeys: dict[int, Monkey] = {}
        self.next_monkey_id = 1
        self.total_monkeys_created = 0

        # Temple entrance and boat landing derived from the temple
        # constants (there is no separate `self.temple` object).
        # Must be set before terrain/monkey generation below, since
        # is_walkable() -> is_inside_temple() reads self.temple_entrance.
        self.temple_entrance = (
            TEMPLE_X + TEMPLE_WIDTH // 2,
            TEMPLE_Y + TEMPLE_HEIGHT - 1,
        )

        self.boat_landing = (
            TEMPLE_X + 25,
            TEMPLE_Y + 10,
        )

        # Generate terrain
        for x in range(width):
            for y in range(height):
                elevation = self._fbm(
                    self.elevation_noise,
                    x,
                    y,
                    ELEVATION_OCTAVES,
                    ELEVATION_BASE_SCALE,
                    ELEVATION_PERSISTENCE,
                    ELEVATION_LACUNARITY,
                )

                elevation -= (
                    self._edge_falloff(x, y) * EDGE_FALLOFF_STRENGTH
                )

                terrain = self._classify(x, y, elevation)
                self.grid[x][y] = Tile(x=x, y=y, terrain=terrain)

        self._thumbnail = self._build_thumbnail()

        for _ in range(100):
            self.spawn_random_monkey()

        # Simulation events
        self.events = []
        self.next_event_id = 1

        # tourists
        self.tourists: list[Tourist] = []
        self.next_tourist_id = 1

        self.last_tourist_boat_day: int | None = None

        self.temple_tourists: set[int] = set()

    # -----------------------------------------------------------------
    # Terrain generation
    # -----------------------------------------------------------------

    def _fbm(
        self,
        noise_obj,
        x,
        y,
        octaves,
        base_scale,
        persistence,
        lacunarity,
    ):
        total = 0.0
        amplitude = 1.0
        frequency = base_scale
        max_amplitude = 0.0

        for _ in range(octaves):
            noise_value = noise_obj.noise2(
                x * frequency,
                y * frequency,
            )

            total += noise_value * amplitude
            max_amplitude += amplitude

            amplitude *= persistence
            frequency *= lacunarity

        return total / max_amplitude

    def _edge_falloff(self, x, y):
        margin = EDGE_FALLOFF_WIDTH * min(
            self.width,
            self.height,
        )

        if margin <= 0:
            return 0.0

        dist_to_edge = min(
            x,
            self.width - 1 - x,
            y,
            self.height - 1 - y,
        )

        return max(0.0, 1.0 - dist_to_edge / margin)

    def _classify(self, x, y, elevation):
        if elevation < WATER_LEVEL:
            return "water"

        if elevation < SAND_LEVEL:
            return "sand"

        if elevation > SNOW_LEVEL:
            return "snow"

        if elevation > MOUNTAIN_LEVEL:
            return "mountain"

        moisture = self._fbm(
            self.moisture_noise,
            x,
            y,
            MOISTURE_OCTAVES,
            MOISTURE_BASE_SCALE,
            MOISTURE_PERSISTENCE,
            MOISTURE_LACUNARITY,
        )

        if moisture > WETLAND_MOISTURE:
            return "wetland"

        if moisture > FOREST_MOISTURE:
            return "forest"

        return "grass"

    # -----------------------------------------------------------------
    # Tiles and walkability
    # -----------------------------------------------------------------

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[x][y]

        return None

    def is_walkable(self, x: int, y: int) -> bool:
        tile = self.get_tile(x, y)

        if tile is None:
            return False

        if self.is_inside_temple(x, y):
            return False

        if tile.terrain in {
            "water",
            "mountain",
            "snow",
        }:
            return False

        return True

    # -----------------------------------------------------------------
    # Tree generation and interaction
    # -----------------------------------------------------------------

    def _tree_should_exist(self, x, y):
        tile = self.grid[x][y]

        if tile.terrain not in ("forest", "grass"):
            return False

        density = self.tree_noise.noise2(
            x * TREE_SCALE,
            y * TREE_SCALE,
        )

        if tile.terrain == "forest":
            threshold = FOREST_TREE_THRESHOLD
        else:
            threshold = GRASS_TREE_THRESHOLD

        return density > threshold

    def _create_tree(self, x, y):
        if self.is_inside_temple(x, y):
            return None

        species_value = self.tree_species_noise.noise2(
            x * TREE_SPECIES_SCALE,
            y * TREE_SPECIES_SCALE,
        )

        if species_value > FRUIT_TREE_THRESHOLD:
            return Tree(
                x=x,
                y=y,
                species="fruit_tree",
                wood=15,
                fruit=8,
                max_fruit=8,
            )

        return Tree(
            x=x,
            y=y,
            species="oak",
            wood=30,
            fruit=0,
            max_fruit=0,
        )

    def _ensure_trees_for_chunk(self, cx, cy):
        # Mutates shared tree state, so this must be locked.
        # Safe to call while already holding the lock because it is RLock.
        with self.lock:
            chunk_key = (cx, cy)

            if chunk_key in self.generated_tree_chunks:
                return

            x0 = cx * self.chunk_size
            y0 = cy * self.chunk_size
            x1 = min(x0 + self.chunk_size, self.width)
            y1 = min(y0 + self.chunk_size, self.height)

            for y in range(y0, y1):
                for x in range(x0, x1):
                    if not self._tree_should_exist(x, y):
                        continue

                    tree = self._create_tree(x, y)

                    if tree is not None:
                        self.trees[(x, y)] = tree

            self.generated_tree_chunks.add(chunk_key)

    def get_tree(self, x, y):
        with self.lock:
            return self.trees.get((x, y))

    def harvest_tree_fruit(self, x, y, amount=1):
        with self.lock:
            tree = self.get_tree(x, y)

            if tree is None:
                return 0

            return tree.harvest_fruit(amount)

    def find_nearest_fruit_tree(self, x, y):
        with self.lock:
            nearest_tree = None
            nearest_distance = None

            for tree in self.trees.values():
                if not tree.alive:
                    continue

                if tree.fruit <= 0:
                    continue

                distance = (
                    abs(tree.x - x)
                    + abs(tree.y - y)
                )

                if (
                    nearest_distance is None
                    or distance < nearest_distance
                ):
                    nearest_tree = tree
                    nearest_distance = distance

            return nearest_tree

    def find_nearest_shelter(self, x, y):
        with self.lock:
            nearest_tree = None
            nearest_distance = None

            for tree in self.trees.values():
                if not tree.alive:
                    continue

                if tree.wood <= 0:
                    continue

                distance = (
                    abs(tree.x - x)
                    + abs(tree.y - y)
                )

                if (
                    nearest_distance is None
                    or distance < nearest_distance
                ):
                    nearest_tree = tree
                    nearest_distance = distance

            return nearest_tree

    def get_visible_fruit_trees(self, x, y, vision_range):
        min_x = max(0, x - vision_range)
        max_x = min(self.width - 1, x + vision_range)

        min_y = max(0, y - vision_range)
        max_y = min(self.height - 1, y + vision_range)

        min_cx = min_x // self.chunk_size
        max_cx = max_x // self.chunk_size

        min_cy = min_y // self.chunk_size
        max_cy = max_y // self.chunk_size

        with self.lock:
            for cy in range(min_cy, max_cy + 1):
                for cx in range(min_cx, max_cx + 1):
                    self._ensure_trees_for_chunk(cx, cy)

            visible = []

            for tree in self.trees.values():
                if not tree.alive:
                    continue

                if tree.fruit <= 0:
                    continue

                distance = max(
                    abs(tree.x - x),
                    abs(tree.y - y),
                )

                if distance <= vision_range:
                    visible.append(tree)

            return visible

    # -----------------------------------------------------------------
    # Monkey spawning and lookup
    # -----------------------------------------------------------------

    def spawn_monkey(self, x, y):
        if not self.is_walkable(x, y):
            return None

        name, gender = generate_monkey_identity()

        with self.lock:
            monkey = Monkey(
                id=self.next_monkey_id,
                name=name,
                gender=gender,
                age=random.randint(0, 350),
                x=x,
                y=y,
                boldness=random_trait(),
                curiosity=random_trait(),
                sociability=random_trait(),
                memory=random_trait(),
                aggression=random_trait(),
            )

            self.add_monkey(monkey)
            self.next_monkey_id += 1

        return monkey

    def add_monkey(self, monkey: Monkey) -> Monkey:
        self.monkeys[monkey.id] = monkey
        self.total_monkeys_created += 1
        return monkey

    def spawn_random_monkey(self, max_attempts=SPAWN_MAX_ATTEMPTS):
        # Picks random tiles until it lands on spawnable ground.
        for _ in range(max_attempts):
            x = random.randrange(self.width)
            y = random.randrange(self.height)

            tile = self.grid[x][y]

            if tile.terrain in SPAWNABLE_TERRAIN_BLOCKLIST:
                continue

            return self.spawn_monkey(x, y)

        return None

    def get_monkeys(self):
        with self.lock:
            return [
                monkey.to_dict()
                for monkey in self.monkeys.values()
            ]

    def get_monkey(self, monkey_id):
        with self.lock:
            return self.monkeys.get(monkey_id)

    def get_monkey_by_id(self, monkey_id):
        with self.lock:
            return self.monkeys.get(monkey_id)

    def create_child_monkey(self, parent_a: Monkey, parent_b: Monkey, ) -> Monkey:
        name, gender = generate_monkey_identity()

        child = Monkey(
            id=self.next_monkey_id,
            x=parent_a.x,
            y=parent_a.y,
            name=name,
            gender=gender,
            age=0,
            parent_ids=(
                parent_a.id,
                parent_b.id,
            ),
            birth_tick=self.total_tick,

            boldness=inherit_trait(
                parent_a.boldness,
                parent_b.boldness,
            ),

            curiosity=inherit_trait(
                parent_a.curiosity,
                parent_b.curiosity,
            ),

            sociability=inherit_trait(
                parent_a.sociability,
                parent_b.sociability,
            ),

            memory=inherit_trait(
                parent_a.memory,
                parent_b.memory,
            ),

            aggression=inherit_trait(
                parent_a.aggression,
                parent_b.aggression,
            ),
        )

        self.next_monkey_id += 1

        return child

    def _handle_reproduction(self):
        monkeys = list(self.monkeys.values())

        paired_ids = set()
        new_monkeys = []

        for monkey in monkeys:
            if monkey.id in paired_ids:
                continue

            if not monkey.can_reproduce(
                self.total_tick,
            ):
                continue

            available_monkeys = [
                other
                for other in monkeys
                if other.id not in paired_ids
            ]

            partner = self.find_reproduction_partner(
                monkey,
                available_monkeys,
            )

            if partner is None:
                continue

            child = self.create_child_monkey(
                monkey,
                partner,
            )

            monkey.energy = max(
                0.0,
                monkey.energy - REPRODUCTION_ENERGY_COST,
            )

            partner.energy = max(
                0.0,
                partner.energy - REPRODUCTION_ENERGY_COST,
            )

            monkey.last_reproduction_tick = (
                self.total_tick
            )

            partner.last_reproduction_tick = (
                self.total_tick
            )

            paired_ids.add(monkey.id)
            paired_ids.add(partner.id)

            new_monkeys.append(child)

            self.add_event(
                event_type="birth",
                message=f"{child.name} was born!",
                data={
                    "child_id": child.id,
                    "parent_ids": [
                        monkey.id,
                        partner.id,
                    ],
                },
            )

        for child in new_monkeys:
            self.add_monkey(child)

    def find_reproduction_partner(
        self,
        monkey: Monkey,
        available_monkeys: list[Monkey],
    ) -> Monkey | None:
        for other in available_monkeys:
            if not monkey.is_compatible_for_reproduction(
                other,
                self.total_tick,
            ):
                continue

            distance = max(
                abs(monkey.x - other.x),
                abs(monkey.y - other.y),
            )

            if distance <= REPRODUCTION_RANGE:
                return other

        return None

    def get_visible_monkeys(self, monkey_id: int, x: int, y: int, vision_range: int):
        visible = []

        for monkey in self.monkeys.values():
            if not monkey.alive:
                continue
            if monkey.id == monkey_id:
                continue
            distance = max(
                abs(monkey.x - x),
                abs(monkey.y - y),
            )
            if distance <= vision_range:
                visible.append(monkey)
        return visible

    # -----------------------------------------------------------------
    # World update and time
    # -----------------------------------------------------------------

    def update(self):
        with self.lock:
            self.tick += 1
            self.total_tick += 1

            if self.tick >= TICKS_PER_DAY:
                self.tick = 0
                self.day += 1


                self._handle_new_day()

            for monkey in self.monkeys.values():
                monkey.update(self)

            self._handle_reproduction()

            dead_ids = [
                monkey_id
                for monkey_id, monkey in self.monkeys.items()
                if not monkey.alive
            ]

            for monkey_id in dead_ids:
                del self.monkeys[monkey_id]

            for tree in self.trees.values():
                tree.update()

            self.update_tourists_arrivals()
            self.update_tourists()

    def add_event(
        self,
        event_type: str,
        message: str,
        data: dict | None = None,
    ):
        event = {
            "id": self.next_event_id,
            "type": event_type,
            "message": message,
            "tick": self.total_tick,
            "day": self.day,
            "data": data or {},
        }

        self.events.append(event)
        self.next_event_id += 1

        # Prevent this growing forever.
        if len(self.events) > 100:
            self.events.pop(0)

    def get_events(self):
        with self.lock:
            return list(self.events)

    def _handle_new_day(self):
        for monkey in self.monkeys.values():
            monkey.age += 1

    def get_hour_of_day(self):
        return (self.tick / TICKS_PER_DAY) * 24

    def is_daytime(self):
        hour = self.get_hour_of_day()
        return 6 <= hour < 18

    def is_nighttime(self):
        hour = self.get_hour_of_day()
        return hour < 6 or hour >= 18

    # -----------------------------------------------------------------
    # World API data
    # -----------------------------------------------------------------

    def meta(self):
        with self.lock:
            return {
                "width": self.width,
                "height": self.height,
                "chunkSize": self.chunk_size,
                "tick": self.tick,
                "day": self.day,
                "hour": round(self.get_hour_of_day(), 1),
                "isDaytime": self.is_daytime(),
                "totalTick": self.total_tick,
            }

    def _build_thumbnail(self, max_dimension=128):
        scale = min(
            1.0,
            max_dimension / max(self.width, self.height),
        )

        thumb_w = max(1, round(self.width * scale))
        thumb_h = max(1, round(self.height * scale))

        chars = []

        for ty in range(thumb_h):
            src_y = min(self.height - 1, int(ty / scale))

            for tx in range(thumb_w):
                src_x = min(self.width - 1, int(tx / scale))
                tile = self.grid[src_x][src_y]

                chars.append(TERRAIN_CODE[tile.terrain])

        return {
            "w": thumb_w,
            "h": thumb_h,
            "terrain": "".join(chars),
        }

    def thumbnail(self):
        return self._thumbnail

    def get_chunk(self, cx, cy):
        x0 = cx * self.chunk_size
        y0 = cy * self.chunk_size

        if (
            x0 >= self.width
            or y0 >= self.height
            or x0 < 0
            or y0 < 0
        ):
            return None

        x1 = min(x0 + self.chunk_size, self.width)
        y1 = min(y0 + self.chunk_size, self.height)

        with self.lock:
            self._ensure_trees_for_chunk(cx, cy)

            chars = []
            trees = []

            for y in range(y0, y1):
                for x in range(x0, x1):
                    tile = self.grid[x][y]
                    chars.append(TERRAIN_CODE[tile.terrain])

                    tree = self.trees.get((x, y))

                    if tree is None or not tree.alive:
                        continue

                    trees.append({
                        "x": tree.x - x0,
                        "y": tree.y - y0,
                        "species": tree.species,
                        "fruit": tree.fruit,
                        "wood": tree.wood,
                        "alive": tree.alive,
                    })

            return {
                "cx": cx,
                "cy": cy,
                "w": x1 - x0,
                "h": y1 - y0,
                "terrain": "".join(chars),
                "trees": trees,
            }

    # -----------------------------------------------------------------
    # Pathfinding
    # -----------------------------------------------------------------

    def find_path(
        self,
        start_x,
        start_y,
        target_x,
        target_y,
    ):
        start = (start_x, start_y)
        target = (target_x, target_y)

        if start == target:
            return []

        open_set = []
        heapq.heappush(open_set, (0, start))

        came_from = {}
        g_score = {start: 0}

        visited = set()

        while open_set:
            _, current = heapq.heappop(open_set)

            if current in visited:
                continue

            visited.add(current)

            if current == target:
                return self._reconstruct_path(
                    came_from,
                    current,
                )

            for neighbour in self._get_path_neighbours(
                current[0],
                current[1],
            ):
                tentative_g_score = g_score[current] + 1

                if tentative_g_score >= g_score.get(
                    neighbour,
                    float("inf"),
                ):
                    continue

                came_from[neighbour] = current
                g_score[neighbour] = tentative_g_score

                heuristic = max(
                    abs(neighbour[0] - target_x),
                    abs(neighbour[1] - target_y),
                )

                priority = tentative_g_score + heuristic

                heapq.heappush(
                    open_set,
                    (priority, neighbour),
                )

        return []

    def _get_path_neighbours(self, x, y):
        neighbours = []

        directions = [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        ]

        for dx, dy in directions:
            next_x = x + dx
            next_y = y + dy

            if not self.is_walkable(
                next_x,
                next_y,
            ):
                continue

            # For diagonal moves, block if both orthogonal corner
            # tiles are blocked.
            if dx != 0 and dy != 0:
                if (
                    not self.is_walkable(x + dx, y)
                    and not self.is_walkable(x, y + dy)
                ):
                    continue

            neighbours.append(
                (next_x, next_y)
            )

        return neighbours

    def _reconstruct_path(
        self,
        came_from,
        current,
    ):
        path = [current]

        while current in came_from:
            current = came_from[current]
            path.append(current)

        path.reverse()

        return path[1:]

    # -----------------------------------------------------------------
    # Temple
    # -----------------------------------------------------------------

    def is_inside_temple(self, x: int, y: int) -> bool:
        # The entrance tile sits on the temple boundary and must stay
        # walkable, or nothing can ever path to it (A* would search the
        # whole reachable map every tick and always fail).
        if (x, y) == self.temple_entrance:
            return False

        return (
            TEMPLE_X <= x < TEMPLE_X + TEMPLE_WIDTH
            and TEMPLE_Y <= y < TEMPLE_Y + TEMPLE_HEIGHT
        )

    def get_temple(self):
        return {
            "x": TEMPLE_X,
            "y": TEMPLE_Y,
            "width": TEMPLE_WIDTH,
            "height": TEMPLE_HEIGHT,
            "entrance": {
                "x": TEMPLE_X + TEMPLE_WIDTH // 2,
                "y": TEMPLE_Y + TEMPLE_HEIGHT - 1,
            },
        }

    # -----------------------------------------------------------------
    # Tourists
    # -----------------------------------------------------------------

    # A boatload arrives clustered near the landing, not stacked on one
    # tile, and each tourist waits a random beat before setting off so
    # they don't walk the identical path in perfect lockstep.
    TOURIST_SPAWN_JITTER_RADIUS = 2
    TOURIST_MAX_SPAWN_DELAY_TICKS = 15

    def spawn_tourists(self, count: int):
        boat_x, boat_y = self.boat_landing
        temple_x, temple_y = self.temple_entrance

        for _ in range(count):
            start = self.get_random_walkable_tile_near(
                boat_x,
                boat_y,
                self.TOURIST_SPAWN_JITTER_RADIUS,
            )

            start_x, start_y = start if start is not None else (boat_x, boat_y)

            tourist = Tourist(
                id=self.next_tourist_id,
                x=start_x,
                y=start_y,
                temple_x=temple_x,
                temple_y=temple_y,
                boat_x=boat_x,
                boat_y=boat_y,
                spawn_delay=random.randint(
                    0,
                    self.TOURIST_MAX_SPAWN_DELAY_TICKS,
                ),
                name=f"Tourist {self.next_tourist_id}",
                value=random.uniform(10.0, 100.0),
                items=generate_tourist_items(),
            )

            self.tourists.append(tourist)
            self.next_tourist_id += 1

    def update_tourists_arrivals(self):
        current_hour = self.get_hour_of_day()

        current_day = self.day
        if current_hour < TOURIST_ARRIVAL_HOUR:
            return

        if self.last_tourist_boat_day == current_day:
            return

        self.spawn_tourists(TOURISTS_PER_DAY)

        self.last_tourist_boat_day = current_day

    def update_tourists(self):
        current_hour = self.get_hour_of_day()

        for tourist in self.tourists:
            tourist.update(
                world=self,
                current_hour=current_hour,
                current_tick=self.tick,
            )

        self.remove_departed_tourists()

    def remove_departed_tourists(self):
        departed_ids = {
            tourist.id for tourist in self.tourists if not tourist.alive
        }
        self.temple_tourists.difference_update(departed_ids)

        self.tourists = [
            tourist for tourist in self.tourists if tourist.alive
        ]

    def try_enter_temple(self, tourist: Tourist) -> bool:
        if tourist.id in self.temple_tourists:
            return True

        if len(self.temple_tourists) >= MAX_TEMPLE_CAPACITY:
            return False

        self.temple_tourists.add(tourist.id)

        tourist.enter_temple(
            current_tick=self.tick,
            ticks_per_hour=max(1, round(TICKS_PER_DAY / 24)),
        )
        return True

    def leave_temple(self, tourist: Tourist):
        self.temple_tourists.discard(tourist.id)

    def get_random_walkable_tile_near(
        self,
        center_x: int,
        center_y: int,
        radius: int,
    ) -> tuple[int, int] | None:
        candidates: list[tuple[int, int]] = []

        min_x = max(0, center_x - radius)
        max_x = min(self.width - 1, center_x + radius)

        min_y = max(0, center_y - radius)
        max_y = min(self.height - 1, center_y + radius)

        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if not self.is_walkable(x, y):
                    continue

                candidates.append((x, y))

        if not candidates:
            return None

        return random.choice(candidates)

    def get_tourists(self):
        with self.lock:
            return [
                {
                    "id": tourist.id,
                    "x": tourist.x,
                    "y": tourist.y,
                    "state": tourist.state,
                    "insideTemple": tourist.inside_temple,
                    "items": [
                        {
                            "name": item.name,
                            "value": item.value,
                        }
                        for item in tourist.items
                    ],
                    "name": tourist.name,
                }
                for tourist in self.tourists
            ]

    def get_tourist(self, tourist_id: int) -> Tourist | None:
            with self.lock:
                for tourist in self.tourists:
                    if tourist.id == tourist_id:
                        return tourist
                return None

    
    
    def get_boat_landing(self):
        x, y = self.boat_landing
        return {"x": x, "y": y}
