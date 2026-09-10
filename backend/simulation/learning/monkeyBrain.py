import torch
import torch.nn as nn


class MonkeyBrain(nn.Module):
    def __init__(self, input_size, output_size):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_size, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, output_size)
        )

    def forward(self, state):
        return self.network(state)



if __name__ == "__main__":
    brain = MonkeyBrain(input_size=18, output_size=15)
    fake_state = torch.tensor([0.5] * 18, dtype=torch.float32) 
    output = brain(fake_state)
    print(len(output))
