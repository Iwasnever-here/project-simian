from dataclasses import dataclass


@dataclass
class Tile:
    x: int
    y: int
    terrain: str