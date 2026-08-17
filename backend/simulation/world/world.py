import heapq
import random
import threading

import opensimplex

from backend.simulation.agents.monkey import Monkey, random_trait
from backend.simulation.names import generate_monkey_identity
from backend.simulation.world.tile import Tile
from backend.simulation.world.tree import Tree


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

        # Monkey state
        self.monkeys: dict[int, Monkey] = {}
        self.next_monkey_id = 1

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
                x=x,
                y=y,
                boldness=random_trait(),
                curiosity=random_trait(),
                sociability=random_trait(),
                memory=random_trait(),
                aggression=random_trait(),
            )

            self.monkeys[monkey.id] = monkey
            self.next_monkey_id += 1

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

    # -----------------------------------------------------------------
    # World update and time
    # -----------------------------------------------------------------

    def update(self):
        with self.lock:
            self.tick += 1

            if self.tick >= TICKS_PER_DAY:
                self.tick = 0
                self.day += 1

                self._handle_new_day()

            for monkey in self.monkeys.values():
                monkey.update(self)

            dead_ids = [
                monkey_id
                for monkey_id, monkey in self.monkeys.items()
                if not monkey.alive
            ]

            for monkey_id in dead_ids:
                del self.monkeys[monkey_id]

            for tree in self.trees.values():
                tree.update()

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