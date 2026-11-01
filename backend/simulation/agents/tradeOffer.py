from dataclasses import dataclass

from .touristItem import TouristItem


@dataclass(frozen=True)
class TradeOffer:
    id: int
    tourist_id: int
    monkey_id: int
    valuable: TouristItem
    food: TouristItem
    expires_at_tick: int
