from dataclasses import dataclass, field


@dataclass
class KnownMonkey:
    monkey_id: int
    last_x: int
    last_y: int
    last_seen_tick: int


@dataclass
class KnownTourist:
    tourist_id: int
    last_x: int
    last_y: int
    last_seen_tick: int
    visible_items: list[str] = field(default_factory=list)


@dataclass
class MonkeyMemory:
    known_monkeys: dict[int, KnownMonkey] = field(
        default_factory=dict
    )
    known_tourists: dict[int, KnownTourist] = field(
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


    def remember_tourist(
        self,
        tourist_id: int,
        x: int,
        y: int,
        current_tick: int,
        visible_items: list[str],
    ):
        self.known_tourists[tourist_id] = KnownTourist(
            tourist_id=tourist_id,
            last_x=x,
            last_y=y,
            last_seen_tick=current_tick,
            visible_items=visible_items,
        )

    def get_tourist(self, tourist_id: int):
        return self.known_tourists.get(tourist_id)