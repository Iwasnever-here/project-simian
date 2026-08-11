from dataclasses import dataclass


@dataclass
class Tree:
    x: int
    y: int
    species: str

    wood: int
    fruit: int
    max_fruit: int

    alive: bool = True

    def harvest_fruit(self, amount: int = 1) -> int:
        if not self.alive:
            return 0

        taken = min(amount, self.fruit)
        self.fruit -= taken

        return taken

    def harvest_wood(self, amount: int) -> int:
        if not self.alive:
            return 0

        taken = min(amount, self.wood)
        self.wood -= taken

        if self.wood <= 0:
            self.alive = False

        return taken

    def regrow_fruit(self, amount: int = 1):
        if not self.alive:
            return

        self.fruit = min(
            self.max_fruit,
            self.fruit + amount,
        )