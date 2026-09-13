# ---------------------------------------------------------------------
# Monkey states
# ---------------------------------------------------------------------

WANDER_STATE = "wandering"
SEEKING_FOOD_STATE = "seeking_food"
EATING_STATE = "eating"
SLEEPING_STATE = "sleeping"
SEEKING_SHELTER_STATE = "seeking_shelter"
FOLLOW_MOTHER_STATE = "following_mother"
APPROACHING_MONKEY_STATE = "approaching_monkey"
AVOIDING_MONKEY_STATE = "avoiding_monkey"
FOLLOWING_MONKEY_STATE = "following_monkey"
CONFRONTING_MONKEY_STATE = "confronting_monkey"
SOCIAL_IDLE_STATE = "socializing"

TOURIST_ACTIONS = [
    "watch",
    "follow",
    "scare",
    "grab_item",
    "leave",
]

MONKEY_ACTIONS = [
    "wander",
    "seek_food",
    "seek_shelter",
    "follow_mother",
    "approach_monkey",
    "avoid_monkey",
    "follow_monkey",
    "confront_monkey",
    "socialise",
    "investigate_tourist",
    "watch_tourist",
    "follow_tourist",
    "scare_tourist",
    "grab_item",
    "leave_tourist",
]


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
TOURIST_INTERACTION_DURATION = 20
TOURIST_INTERACTION_COOLDOWN_TICKS = 30


HUNGER_REWARD_WEIGHT = 1.0
ENERGY_REWARD_WEIGHT = 0.1
HEALTH_REWARD_WEIGHT = 1.0

MAX_EXPERIENCES = 1000

EPSILON = 0.1
