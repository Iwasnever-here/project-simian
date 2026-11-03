from dataclasses import dataclass


@dataclass
class Experience:
    state: list[float]
    action: int
    reward: float
    next_state: list[float]
    done: bool
    next_valid_actions: tuple[int, ...] = ()
