from dataclasses import dataclass
import random


@dataclass
class TouristItem:
    name: str
    value: float
    kind: str
    hunger_restore: float | None = None


TOURIST_ITEM_TYPES = [
    TouristItem(
        name="banana",
        value=1.0,
        kind="food",
        hunger_restore=30.0,
    ),
    TouristItem(
        name="snack",
        value=0.5,
        kind="food",
        hunger_restore=20.0,
    ),
    TouristItem(
        name="sunglasses",
        value=2.0,
        kind="valuable",
    ),
    TouristItem(
        name="phone",
        value=3.0,
        kind="valuable",
    ),
    TouristItem(
        name="camera",
        value=5.0,
        kind="valuable",
    ),
    TouristItem(
        name="bag",
        value=1.5,
        kind="valuable",
    ),
]


def generate_tourist_items() -> list[TouristItem]:
    item_count = random.randint(1, 3)

    return random.sample(
        TOURIST_ITEM_TYPES,
        item_count,
    )