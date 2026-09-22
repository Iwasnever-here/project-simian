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

FOREST_TREE_THRESHOLD = 0.10
GRASS_TREE_THRESHOLD = 0.30
FRUIT_TREE_THRESHOLD = -0.30



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