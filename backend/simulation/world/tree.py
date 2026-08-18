from dataclasses import dataclass


MAX_FRUIT = 5
FRUIT_REGROW_TICKS = 200

@dataclass
class Tree:
    x: int
    y: int
    species: str

    wood: int
    fruit: int
    max_fruit: int = MAX_FRUIT
    ticks_since_regrow: int = 0

    alive: bool = True

    def harvest_fruit(self, amount: int = 1) -> int:
        if not self.alive:
            return 0

        taken = min(amount, self.fruit)
        self.fruit -= taken

        return taken

    def regrow_fruit(self, amount: int = 1):
        if not self.alive:
            return

        self.fruit = min(
            self.max_fruit,
            self.fruit + amount,
        )

    def update(self):
        if self.fruit >= self.max_fruit:
            self.ticks_since_regrow = 0
            return
        self.ticks_since_regrow += 1

        if self.ticks_since_regrow >= FRUIT_REGROW_TICKS:
            self.fruit += 1
            self.ticks_since_regrow = 0