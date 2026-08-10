import opensimplex
from backend.simulation.world.tile import Tile

CHUNK_SIZE = 32

# Single-char codes keep chunk payloads small (no repeated x/y/terrain keys)
TERRAIN_CODE = {
    "water": "w",
    "sand": "s",
    "grass": "g",
}

# How far in from the edge (as a fraction of the shorter map dimension) the
# water falloff extends. 0.15 = water dominates the outer 15% of the map.
EDGE_FALLOFF_WIDTH = 0.15
# How strongly the falloff pulls noise values down near the edge. Higher =
# harder guarantee of water right at the border, regardless of noise value.
EDGE_FALLOFF_STRENGTH = 1.4

# Terrain thresholds - noise2() ranges roughly [-1, 1]. Lower WATER_THRESHOLD
# and SAND_THRESHOLD to shrink water/sand and let grass cover more of the map.
WATER_THRESHOLD = -0.65
SAND_THRESHOLD = -0.35


class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.chunk_size = CHUNK_SIZE

        # opensimplex, and seed selection
        self.noise = opensimplex.OpenSimplex(seed=12345)

        scale = 0.1  # scale for the noise function

        # 2D grid indexed [x][y] -> O(1) lookup instead of scanning a flat list
        self.grid = [[None] * height for _ in range(width)]
        for x in range(width):
            for y in range(height):
                noise_value = self.noise.noise2(x * scale, y * scale)
                noise_value -= self._edge_falloff(x, y) * EDGE_FALLOFF_STRENGTH

                if noise_value < WATER_THRESHOLD:
                    terrain = "water"
                elif noise_value < SAND_THRESHOLD:
                    terrain = "sand"
                else:
                    terrain = "grass"
                self.grid[x][y] = Tile(x, y, terrain)

    def _edge_falloff(self, x, y):
        # Normalized distance from the nearest edge: 0 at the border, 1 once
        # you're EDGE_FALLOFF_WIDTH (or more) of the way toward the center.
        margin = EDGE_FALLOFF_WIDTH * min(self.width, self.height)
        if margin <= 0:
            return 0.0

        dist_to_edge = min(x, self.width - 1 - x, y, self.height - 1 - y)
        closeness = max(0.0, 1.0 - dist_to_edge / margin)  # 1 at edge, 0 inland
        return closeness

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[x][y]
        return None

    def meta(self):
        # Lightweight payload the frontend fetches once on load
        return {
            "width": self.width,
            "height": self.height,
            "chunkSize": self.chunk_size,
        }

    def get_chunk(self, cx, cy):
        # Bounding box for this chunk, clipped to world edges (for partial edge chunks)
        x0 = cx * self.chunk_size
        y0 = cy * self.chunk_size
        x1 = min(x0 + self.chunk_size, self.width)
        y1 = min(y0 + self.chunk_size, self.height)

        chars = []
        for y in range(y0, y1):
            for x in range(x0, x1):
                chars.append(TERRAIN_CODE[self.grid[x][y].terrain])

        return {
            "cx": cx,
            "cy": cy,
            "w": x1 - x0,
            "h": y1 - y0,
            "terrain": "".join(chars),  # row-major, e.g. "wwssggg..."
        }