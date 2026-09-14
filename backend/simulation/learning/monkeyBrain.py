import torch
import torch.nn as nn

from backend.simulation.agents.monkey.monkey_constants import (
    LEARNING_RATE,
)


class MonkeyBrain(nn.Module):
    def __init__(self, input_size, output_size):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_size, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, output_size),
        )

        self.optimizer = torch.optim.Adam(
            self.parameters(),
            lr=LEARNING_RATE,
        )

    def forward(self, state):
        return self.network(state)