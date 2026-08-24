from dataclasses import dataclass
import random


@dataclass
class TouristItem:
    name: str
    value: float


TOURIST_ITEM_TYPES = [
    TouristItem("banana", 1.0),
    TouristItem("snack", 0.5),
    TouristItem("sunglasses", 2.0),
    TouristItem("phone", 3.0),
    TouristItem("camera", 5.0),
    TouristItem("bag", 1.5),
]


def generate_tourist_items() -> list[TouristItem]:
    item_count = random.randint(1, 3)

    return random.sample(
        TOURIST_ITEM_TYPES,
        item_count,
    )