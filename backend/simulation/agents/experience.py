from dataclasses import dataclass


@dataclass
class Experience:
    state: list[float]
    action: int
    reward: float
    next_state: list[float]