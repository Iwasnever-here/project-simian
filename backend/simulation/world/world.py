import opensimplex

from backend.simulation.world.tile import Tile
from backend.simulation.world.tree import Tree


CHUNK_SIZE = 32


# Single-char codes keep chunk payloads small
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

FOREST_TREE_THRESHOLD = 0.2
GRASS_TREE_THRESHOLD = 0.6


class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.chunk_size = CHUNK_SIZE

        self.elevation_noise = opensimplex.OpenSimplex(
            seed=12345
        )

        self.moisture_noise = opensimplex.OpenSimplex(
            seed=98765
        )

        self.tree_noise = opensimplex.OpenSimplex(
            seed=54321
        )

        # Terrain is still generated once at startup.
        #
        # Trees are NOT generated here anymore.
        # They are generated only when a chunk is requested.
        self.grid = [
            [None] * height
            for _ in range(width)
        ]

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
                    self._edge_falloff(x, y)
                    * EDGE_FALLOFF_STRENGTH
                )

                terrain = self._classify(
                    x,
                    y,
                    elevation,
                )

                self.grid[x][y] = Tile(
                    x,
                    y,
                    terrain,
                )

        self._thumbnail = self._build_thumbnail()

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
            total += (
                noise_obj.noise2(
                    x * frequency,
                    y * frequency,
                )
                * amplitude
            )

            max_amplitude += amplitude

            amplitude *= persistence
            frequency *= lacunarity

        return total / max_amplitude

    def _edge_falloff(self, x, y):
        margin = (
            EDGE_FALLOFF_WIDTH
            * min(self.width, self.height)
        )

        if margin <= 0:
            return 0.0

        dist_to_edge = min(
            x,
            self.width - 1 - x,
            y,
            self.height - 1 - y,
        )

        closeness = max(
            0.0,
            1.0 - dist_to_edge / margin,
        )

        return closeness

    def _classify(
        self,
        x,
        y,
        elevation,
    ):
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

    def _tree_at(
        self,
        x,
        y,
    ):
        tile = self.grid[x][y]

        if tile.terrain not in (
            "forest",
            "grass",
        ):
            return None

        density = self.tree_noise.noise2(
            x * TREE_SCALE,
            y * TREE_SCALE,
        )

        if tile.terrain == "forest":
            threshold = FOREST_TREE_THRESHOLD
        else:
            threshold = GRASS_TREE_THRESHOLD

        if density <= threshold:
            return None

        return Tree(
            x=x,
            y=y,
            species="oak",
        )

    def _build_thumbnail(
        self,
        max_dimension=128,
    ):
        scale = min(
            1.0,
            max_dimension
            / max(
                self.width,
                self.height,
            ),
        )

        thumb_w = max(
            1,
            round(
                self.width * scale
            ),
        )

        thumb_h = max(
            1,
            round(
                self.height * scale
            ),
        )

        chars = []

        for ty in range(thumb_h):
            src_y = min(
                self.height - 1,
                int(ty / scale),
            )

            for tx in range(thumb_w):
                src_x = min(
                    self.width - 1,
                    int(tx / scale),
                )

                tile = self.grid[
                    src_x
                ][
                    src_y
                ]

                chars.append(
                    TERRAIN_CODE[
                        tile.terrain
                    ]
                )

        return {
            "w": thumb_w,
            "h": thumb_h,
            "terrain": "".join(chars),
        }

    def get_tile(
        self,
        x,
        y,
    ):
        if (
            0 <= x < self.width
            and 0 <= y < self.height
        ):
            return self.grid[x][y]

        return None

    def meta(self):
        return {
            "width": self.width,
            "height": self.height,
            "chunkSize": self.chunk_size,
        }

    def get_chunk(
        self,
        cx,
        cy,
    ):
        x0 = cx * self.chunk_size
        y0 = cy * self.chunk_size

        if (
            x0 >= self.width
            or y0 >= self.height
            or x0 < 0
            or y0 < 0
        ):
            return None

        x1 = min(
            x0 + self.chunk_size,
            self.width,
        )

        y1 = min(
            y0 + self.chunk_size,
            self.height,
        )

        chars = []
        trees = []

        for y in range(y0, y1):
            for x in range(x0, x1):
                tile = self.grid[x][y]

                chars.append(
                    TERRAIN_CODE[
                        tile.terrain
                    ]
                )

                tree = self._tree_at(
                    x,
                    y,
                )

                if tree is not None:
                    trees.append({
                        # Coordinates relative
                        # to this chunk.
                        "x": tree.x - x0,
                        "y": tree.y - y0,
                        "species": tree.species,
                    })

        return {
            "cx": cx,
            "cy": cy,
            "w": x1 - x0,
            "h": y1 - y0,
            "terrain": "".join(chars),
            "trees": trees,
        }

    def thumbnail(self):
        return self._thumbnail