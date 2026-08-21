from dataclasses import dataclass, field


@dataclass
class KnownMonkey:
    monkey_id: int
    last_x: int
    last_y: int
    last_seen_tick: int


@dataclass
class MonkeyMemory:
    known_monkeys: dict[int, KnownMonkey] = field(
        default_factory=dict
    )

    def remember(
        self,
        monkey_id: int,
        x: int,
        y: int,
        current_tick: int,
    ):
        self.known_monkeys[monkey_id] = KnownMonkey(
            monkey_id=monkey_id,
            last_x=x,
            last_y=y,
            last_seen_tick=current_tick,
        )

    def get(self, monkey_id: int):
        return self.known_monkeys.get(monkey_id)