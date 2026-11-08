import importlib
import threading
from collections import defaultdict
from dataclasses import replace
from unittest.mock import patch

import pytest
import torch
from fastapi.testclient import TestClient

from backend.simulation.world.world import World
from backend.simulation.agents.monkey.monkey import Monkey
from backend.simulation.agents.monkey import monkey_learning as learning
from backend.simulation.agents.monkey.monkey_constants import MONKEY_ACTIONS
from backend.simulation.agents.monkey.monkey_tourists import execute_trade_action, steal_item
from backend.simulation.agents.touristItem import TouristItem
from backend.simulation.agents.tourists import (
    Tourist, HEADING_TO_BOAT, FLEEING_MONKEY, TRADE_RETRY_COOLDOWN_TICKS,
)


@pytest.fixture
def scene():
    world = World.__new__(World)
    world.lock = threading.RLock()
    world.total_tick = 10
    world.tick = 10
    world.day = 45
    world.events = []
    world.next_event_id = 1
    world.trade_offers = {}
    world.next_trade_offer_id = 1
    monkey = Monkey(1, 0, 0, "male", "Thief", hunger=70, age=150)
    tourist = Tourist(1, "Visitor", 10, 3, 0, 0, 0, 0, 0)
    valuable = TouristItem("phone", 3, "valuable")
    food = TouristItem("banana", 1, "food", 30)
    tourist.items = [valuable, food]
    tourist.path = [(4, 0)]
    world.monkeys = {1: monkey}
    world.tourists = [tourist]
    world.temple_tourists = set()
    world.get_hour_of_day = lambda: 12
    world.find_path = lambda x, y, tx, ty: [(tx, ty)]
    world.is_walkable = lambda x, y: True
    world.get_visible_fruit_trees = lambda *args: []
    world.update_tourists_arrivals = lambda: None
    world.trees = {}
    world.pending_births = []
    world.profile = defaultdict(float)
    world.profile_samples = 0
    world.monkey_profile = defaultdict(float)
    world.monkey_profile_samples = 0
    world.brain_action_counts = defaultdict(int)
    world.brain_action_samples = 0
    world.deaths_since_demographic_log = {}
    return world, monkey, tourist, valuable, food


def take_valuable(scene):
    world, monkey, tourist, valuable, _ = scene
    assert world.transfer_item_to_monkey(monkey, tourist, valuable)


@pytest.mark.parametrize("item_value,expected", [(0.5, None), (1, "banana"), (3, "crisps"), (20, "ice cream")])
def test_offers_use_value_budget_and_real_inventory(scene, item_value, expected):
    world, monkey, tourist, valuable, food = scene
    valuable.value = item_value
    tourist.items += [TouristItem("crisps", 2, "food", 30), TouristItem("ice cream", 9, "food", 50)]
    take_valuable(scene)
    assert tourist.try_offer_trade(world) is (expected is not None)
    offer = world.get_trade_offer_for_monkey(monkey, [tourist])
    if expected is None:
        assert offer is None
    else:
        assert offer.food.name == expected
        assert offer.food in tourist.items
        assert offer.food.value <= valuable.value
        assert offer.valuable is valuable
        assert valuable in monkey.held_items


@pytest.mark.parametrize("invalid", ["far", "missing_valuable", "no_food", "dead_monkey", "wrong_thief", "bad_food"])
def test_tourist_does_not_offer_invalid_trades(scene, invalid):
    world, monkey, tourist, valuable, food = scene
    take_valuable(scene)
    if invalid == "far": monkey.x = 20
    elif invalid == "missing_valuable": monkey.held_items.clear()
    elif invalid == "no_food": tourist.items.clear()
    elif invalid == "dead_monkey": monkey.alive = False
    elif invalid == "wrong_thief": tourist.stolen_valuables[valuable] = 999
    elif invalid == "bad_food": food.hunger_restore = float("nan")
    assert not tourist.try_offer_trade(world)
    assert not world.trade_offers


def test_tourist_update_creates_one_offer_and_waits(scene):
    world, monkey, tourist, _, _ = scene
    take_valuable(scene)
    tourist.update(world, 12, world.tick)
    offer = world.get_trade_offer_for_monkey(monkey, [tourist])
    assert offer is not None
    assert tourist.x == 3
    assert tourist.path == [(4, 0)]
    tourist.update(world, 12, world.tick)
    assert list(world.trade_offers) == [offer.id]
    assert tourist.x == 3


def test_pending_offer_is_visible_in_both_inspectors(scene, monkeypatch):
    world, monkey, tourist, valuable, food = scene
    take_valuable(scene)
    assert tourist.try_offer_trade(world)
    offer = world.get_trade_offer_for_monkey(monkey, [tourist])
    with patch("backend.simulation.world.world.World", return_value=world):
        api = importlib.import_module("backend.api.main")
    monkeypatch.setattr(api, "world", world)
    client = TestClient(api.app)
    routes = [f"/monkeys/{monkey.id}", f"/tourists/{tourist.id}"]
    world.total_tick += 1
    for route in routes:
        response = client.get(route)
        assert response.status_code == 200
        assert response.json()["pending_trade_offer"] == {
            "id": offer.id,
            "monkey_name": monkey.name,
            "tourist_name": tourist.name,
            "item_name": valuable.name,
            "food_name": food.name,
            "ticks_remaining": 29,
        }
    world.total_tick = offer.expires_at_tick
    for route in routes:
        assert client.get(route).json()["pending_trade_offer"] is None
    assert offer.id in world.trade_offers  # Inspection leaves lifecycle changes to the simulation.


@pytest.mark.parametrize("outcome", ["reject", "expire"])
def test_rejection_and_expiry_delay_retry(scene, outcome):
    world, monkey, tourist, _, _ = scene
    take_valuable(scene)
    assert tourist.try_offer_trade(world)
    offer = world.get_trade_offer_for_monkey(monkey, [tourist])
    if outcome == "reject":
        assert world.reject_trade_offer(monkey, offer.id)
    else:
        world.total_tick = offer.expires_at_tick
        world._expire_trade_offers()
    assert not tourist.try_offer_trade(world)
    world.total_tick += TRADE_RETRY_COOLDOWN_TICKS - 1
    assert not tourist.try_offer_trade(world)
    world.total_tick += 1
    assert tourist.try_offer_trade(world)
    assert world.get_trade_offer_for_monkey(monkey, [tourist]).id != offer.id


@pytest.mark.parametrize("priority", ["boat", "flee"])
def test_departure_and_fleeing_interrupt_pending_offer(scene, priority):
    world, monkey, tourist, _, _ = scene
    take_valuable(scene)
    assert tourist.try_offer_trade(world)
    if priority == "flee":
        monkey.state = "scaring_tourist"
        monkey.target_tourist_id = tourist.id
    tourist.update(world, 17 if priority == "boat" else 12, world.tick)
    assert tourist.state == (HEADING_TO_BOAT if priority == "boat" else FLEEING_MONKEY)
    assert not world.trade_offers


def test_offer_visibility_ownership_cooldown_and_curriculum(scene):
    world, monkey, tourist, _, _ = scene
    take_valuable(scene)
    monkey.target_tourist_id = None
    monkey.tourist_interaction_cooldown = 30
    assert tourist.try_offer_trade(world)
    assert world.get_trade_offer_for_monkey(monkey, []) is None
    impostor = Monkey(1, 0, 0, "male", "Impostor")
    assert world.get_trade_offer_for_monkey(impostor, [tourist]) is None
    actions = learning.get_valid_actions(monkey, world, [], [], [tourist])
    assert "accept_trade" in actions and "reject_trade" in actions
    world.day = 44
    assert "accept_trade" not in learning.get_valid_actions(monkey, world, [], [], [tourist])
    world.day = 45
    state = learning.get_brain_state(monkey, world, [], [], [tourist])
    assert state[-2:] == [1.0, 0.3]
    assert len(state) == monkey.brain.network[0].in_features
    assert len(learning.get_brain_output(monkey, state)) == len(MONKEY_ACTIONS)
    tourist.x = 10
    assert world.get_trade_offer_for_monkey(monkey, [tourist]) is None
    assert "accept_trade" not in learning.get_valid_actions(monkey, world, [], [], [tourist])


def test_departure_time_invalidates_offer_before_tourist_update(scene):
    world, monkey, tourist, valuable, food = scene
    take_valuable(scene)
    assert tourist.try_offer_trade(world)
    offer = world.get_trade_offer_for_monkey(monkey, [tourist])
    world.get_hour_of_day = lambda: 17
    assert world.get_trade_offer_for_monkey(monkey, [tourist]) is None
    assert not world.accept_trade_offer(monkey, offer.id)
    assert valuable in monkey.held_items and food in tourist.items


def test_dispatch_uses_exact_offer_id_and_returns_exact_item_once(scene):
    world, monkey, tourist, valuable, food = scene
    take_valuable(scene)
    duplicate = replace(valuable)
    monkey.held_items.append(duplicate)
    assert tourist.try_offer_trade(world)
    offer = world.get_trade_offer_for_monkey(monkey, [tourist])
    assert not execute_trade_action(monkey, world, offer.id + 1, "accept_trade", [tourist])
    assert not execute_trade_action(monkey, world, offer.id, "accept_trade", [])
    assert execute_trade_action(monkey, world, offer.id, "accept_trade", [tourist])
    assert valuable in tourist.items
    assert food not in tourist.items
    assert monkey.held_items == [duplicate]
    assert monkey.hunger == 40
    assert not execute_trade_action(monkey, world, offer.id, "accept_trade", [tourist])
    assert monkey.hunger == 40


@pytest.mark.parametrize("action", ["accept_trade", "reject_trade"])
def test_world_ticks_wire_theft_offer_brain_response_and_training(scene, monkeypatch, action):
    world, monkey, tourist, valuable, food = scene
    # Use the real theft action: it clears the target and starts the cooldown.
    monkeypatch.setattr("random.choice", lambda items: items[0])
    assert steal_item(monkey, world, tourist)
    assert monkey.target_tourist_id is None
    assert monkey.tourist_interaction_cooldown == 30
    monkeypatch.setattr(learning, "EPSILON", 0.0)
    monkeypatch.setattr(learning, "DEBUG_FAVOUR_STEALING", False)
    with torch.no_grad():
        for parameter in monkey.brain.parameters():
            parameter.zero_()
        monkey.brain.network[-1].bias.fill_(-10)
        monkey.brain.network[-1].bias[MONKEY_ACTIONS.index("wander")] = 0
        monkey.brain.network[-1].bias[MONKEY_ACTIONS.index(action)] = 10
    monkey._wander = lambda world: None
    # First real world tick: tourists propose after monkeys update.
    world.update()
    offer = world.get_trade_offer_for_monkey(monkey, [tourist])
    assert offer is not None
    # Make sure urgent-food continuation does not suppress accepting a deal.
    if action == "accept_trade":
        monkey.last_brain_action = "seek_food"
        monkey.target_x, monkey.target_y = 10, 10
    before = monkey.hunger
    world.update()
    assert not world.trade_offers
    preceding_experience = monkey.brain_experiences[-1]
    assert preceding_experience.state[-2:] == [0.0, 0.0]
    assert preceding_experience.next_state[-2:] == [1.0, 0.3]
    assert MONKEY_ACTIONS.index(action) in preceding_experience.next_valid_actions
    assert monkey.pending_brain_action == MONKEY_ACTIONS.index(action)
    if action == "accept_trade":
        assert valuable in tourist.items and valuable not in monkey.held_items
        assert food not in tourist.items
        assert monkey.hunger == pytest.approx(before + 0.25 - food.hunger_restore)
        assert monkey.pending_brain_reward > 0
    else:
        assert valuable in monkey.held_items and food in tourist.items

    reward = monkey.pending_brain_reward
    world.update()
    experience = monkey.brain_experiences[-1]
    assert experience.action == MONKEY_ACTIONS.index(action)
    assert experience.reward == reward
    assert experience.state == preceding_experience.next_state
    assert len(experience.next_state) == 21
    # Exercise a real optimizer step with the expanded state and action dimensions.
    monkey.brain_experiences *= 32
    assert torch.isfinite(torch.tensor(learning.train_brain(monkey)))
