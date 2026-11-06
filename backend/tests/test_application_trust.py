import importlib
import threading
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import torch
from fastapi.testclient import TestClient

from backend.simulation.world.world import World
from backend.simulation.agents.experience import Experience
from backend.simulation.agents.monkey.monkey import Monkey
from backend.simulation.agents.monkey import monkey_learning as learning
from backend.simulation.agents.monkey.monkey_constants import MONKEY_ACTIONS


@pytest.fixture
def scene():
    monkey = Monkey(id=1, x=0, y=0, gender="male", name="Test")
    world = SimpleNamespace(
        lock=threading.RLock(), day=0, total_tick=10,
        is_daytime=lambda: True,
        get_monkey=lambda identifier: monkey if identifier == 1 else None,
        get_visible_fruit_trees=lambda *args: [],
        get_visible_monkeys=lambda *args: [],
        get_visible_tourists=lambda *args: [],
        get_trade_offer_for_monkey=lambda *args: None,
    )
    return monkey, world


@pytest.mark.parametrize("endpoint,key", [
    ("brain-state", "brain_state"),
    ("brain-output", "outputs"),
    ("brain-choice", "chosen_action"),
    ("brain-debug", "q_values"),
])
def test_brain_endpoints(scene, monkeypatch, endpoint, key):
    _, world = scene
    # Keep API smoke tests small and do not start the simulation loop.
    with patch("backend.simulation.world.world.World", return_value=world):
        api = importlib.import_module("backend.api.main")
    monkeypatch.setattr(api, "world", world)
    client = TestClient(api.app)
    response = client.get(f"/monkeys/1/{endpoint}")
    assert response.status_code == 200
    payload = response.json()
    assert key in payload
    if endpoint == "brain-state":
        assert len(payload[key]) == 21
    elif endpoint == "brain-output":
        assert len(payload[key]) == len(MONKEY_ACTIONS)
    elif endpoint == "brain-choice":
        assert payload[key] in payload["valid_actions"]
    assert client.get(f"/monkeys/999/{endpoint}").status_code == 404


@pytest.mark.parametrize("alive", [True, False])
def test_monkey_api_reports_alive_status(scene, monkeypatch, alive):
    monkey, world = scene
    monkey.alive = alive
    with patch("backend.simulation.world.world.World", return_value=world):
        api = importlib.import_module("backend.api.main")
    monkeypatch.setattr(api, "world", world)
    response = TestClient(api.app).get("/monkeys/1")
    assert response.status_code == 200
    assert response.json()["alive"] is alive


@pytest.mark.parametrize("alive", [True, False])
def test_experience_records_curriculum_filtered_next_actions(scene, alive):
    monkey, world = scene
    monkey.alive = alive
    monkey.pending_brain_state = [0.0] * 21
    monkey.pending_brain_action = 0
    # Social actions are visible but unavailable in day-zero curriculum.
    world.get_visible_monkeys = lambda *args: [
        SimpleNamespace(id=2, x=1, y=0),
    ]
    learning.finalize_brain_experience(monkey, world)
    experience = monkey.brain_experiences[-1]
    assert experience.done is (not alive)
    assert experience.next_valid_actions == ((0,) if alive else ())


@pytest.mark.parametrize("done,valid,expected_loss", [
    (False, (1,), 9.0),
    (True, (1,), 1.0),
    (False, (), 1.0),
    (True, (), 1.0),
])
def test_training_ignores_unavailable_actions(monkeypatch, done, valid, expected_loss):
    monkeypatch.setattr(learning, "BATCH_SIZE", 1)
    monkeypatch.setattr(learning, "MIN_TRAINING_EXPERIENCES", 1)
    monkeypatch.setattr(learning, "GAMMA", 1.0)
    brain = torch.nn.Linear(1, len(MONKEY_ACTIONS))
    with torch.no_grad():
        brain.weight.zero_()
        brain.bias.fill_(100.0)  # Invalid actions must not inflate the target.
        brain.bias[0] = 0.0
        brain.bias[1] = 2.0
    brain.optimizer = torch.optim.SGD(brain.parameters(), lr=0.01)
    monkey = SimpleNamespace(
        brain=brain,
        brain_experiences=[Experience([0.0], 0, 1.0, [0.0], done, valid)],
    )
    assert learning.train_brain(monkey) == pytest.approx(expected_loss)


def test_stealing_bias_is_configurable_and_respects_valid_actions(monkeypatch):
    with monkeypatch.context() as config:
        config.delenv("SIMIAN_DEBUG_FAVOUR_STEALING", raising=False)
        importlib.reload(learning)
        assert learning.DEBUG_FAVOUR_STEALING is False
        config.setenv("SIMIAN_DEBUG_FAVOUR_STEALING", "true")
        importlib.reload(learning)
        assert learning.DEBUG_FAVOUR_STEALING is True
    importlib.reload(learning)

    monkeypatch.setattr(learning, "get_brain_output", lambda *args: torch.zeros(len(MONKEY_ACTIONS)))
    monkeypatch.setattr(learning.random, "random", lambda: 0.25)
    monkeypatch.setattr(learning, "DEBUG_FAVOUR_STEALING", False)
    assert learning.choose_brain_action(None, [], ["wander", "steal_item"]) == "wander"
    monkeypatch.setattr(learning, "DEBUG_FAVOUR_STEALING", True)
    assert learning.choose_brain_action(None, [], ["wander", "steal_item"]) == "steal_item"
    assert learning.choose_brain_action(None, [], ["wander"]) == "wander"
