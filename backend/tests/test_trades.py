import threading
from dataclasses import replace

import pytest

from backend.simulation.world.world import World
from backend.simulation.agents.monkey.monkey import Monkey
from backend.simulation.agents.monkey.monkey_tourists import steal_item
from backend.simulation.agents.tourists import Tourist
from backend.simulation.agents.touristItem import (
    TouristItem, TOURIST_ITEM_TYPES, generate_tourist_items,
)


@pytest.fixture
def trade():
    # Avoid terrain generation and spawning 300 brains in unit tests.
    world = World.__new__(World)
    world.lock = threading.RLock()
    world.total_tick = 10
    world.tick = 10
    world.trade_offers = {}
    world.next_trade_offer_id = 1
    monkey = Monkey(id=1, x=0, y=0, gender="male", name="Thief", hunger=70)
    tourist = Tourist(1, "Visitor", 1, 3, 0, 0, 0, 0, 0)
    valuable = TouristItem("phone", 3, "valuable")
    food = TouristItem("banana", 1, "food", 30)
    tourist.items = [valuable, food]
    world.monkeys = {monkey.id: monkey}
    world.tourists = [tourist]
    assert world.transfer_item_to_monkey(monkey, tourist, valuable)
    return world, monkey, tourist, valuable, food


def test_inventory_items_are_distinct(monkeypatch):
    monkeypatch.setattr("random.sample", lambda population, count: population[:2])
    first, second = generate_tourist_items(), generate_tourist_items()
    assert first[0] is not second[0]
    assert first[0] is not TOURIST_ITEM_TYPES[0]
    assert first[0] != second[0]
    assert first[0].name == second[0].name


def test_accept_returns_exact_valuable_and_consumes_food_once(trade):
    world, monkey, tourist, valuable, food = trade
    identical = replace(valuable)
    monkey.held_items.insert(0, identical)
    assert tourist.stolen_valuables[valuable] == monkey.id
    offer = world.create_trade_offer(tourist, monkey, valuable, food)
    assert world.create_trade_offer(tourist, monkey, valuable, food) is None
    assert world.accept_trade_offer(monkey, offer.id)
    assert tourist.items == [valuable]
    assert monkey.held_items == [identical]
    assert monkey.hunger == 40
    assert valuable not in tourist.stolen_valuables
    assert not world.accept_trade_offer(monkey, offer.id)
    assert not world.reject_trade_offer(monkey, offer.id)
    assert monkey.hunger == 40


def test_reject_keeps_inventories_and_hunger(trade):
    world, monkey, tourist, valuable, food = trade
    offer = world.create_trade_offer(tourist, monkey, valuable, food)
    assert world.reject_trade_offer(monkey, offer.id)
    assert monkey.held_items == [valuable]
    assert tourist.items == [food]
    assert monkey.hunger == 70
    assert tourist.stolen_valuables[valuable] == monkey.id
    assert not world.accept_trade_offer(monkey, offer.id)


@pytest.mark.parametrize("invalid", [
    "distance", "missing_food", "missing_valuable", "wrong_owner",
    "dead_monkey", "dead_tourist", "inside_temple", "removed_tourist",
    "bad_food", "nan_food", "wrong_kind", "expired",
])
def test_invalid_acceptance_does_not_transfer(trade, invalid):
    world, monkey, tourist, valuable, food = trade
    offer = world.create_trade_offer(tourist, monkey, valuable, food)
    if invalid == "distance":
        tourist.x = 4
    elif invalid == "missing_food":
        tourist.items.clear()
    elif invalid == "missing_valuable":
        monkey.held_items.clear()
    elif invalid == "wrong_owner":
        tourist.stolen_valuables[valuable] = 999
    elif invalid == "dead_monkey":
        monkey.alive = False
    elif invalid == "dead_tourist":
        tourist.alive = False
    elif invalid == "inside_temple":
        tourist.inside_temple = True
    elif invalid == "removed_tourist":
        world.tourists.clear()
    elif invalid == "bad_food":
        food.hunger_restore = 0
    elif invalid == "nan_food":
        food.hunger_restore = float("nan")
    elif invalid == "wrong_kind":
        food.kind = "valuable"
    elif invalid == "expired":
        world.total_tick = offer.expires_at_tick
    before = (list(monkey.held_items), list(tourist.items), monkey.hunger)
    assert not world.accept_trade_offer(monkey, offer.id)
    assert (monkey.held_items, tourist.items, monkey.hunger) == before
    assert offer.id not in world.trade_offers


def test_forged_items_and_wrong_monkey_cannot_trade(trade):
    world, monkey, tourist, valuable, food = trade
    assert world.create_trade_offer(tourist, monkey, replace(valuable), food) is None
    assert world.create_trade_offer(tourist, monkey, valuable, replace(food)) is None
    offer = world.create_trade_offer(tourist, monkey, valuable, food)
    impostor = Monkey(id=monkey.id, x=0, y=0, gender="male", name="Other")
    assert not world.accept_trade_offer(impostor, offer.id)
    assert not world.reject_trade_offer(impostor, offer.id)
    assert world.accept_trade_offer(monkey, offer.id)


def test_expired_offer_does_not_block_new_offer(trade):
    world, monkey, tourist, valuable, food = trade
    old = world.create_trade_offer(tourist, monkey, valuable, food)
    world.total_tick = old.expires_at_tick
    new = world.create_trade_offer(tourist, monkey, valuable, food)
    assert new.id != old.id
    assert not world.accept_trade_offer(monkey, old.id)
    assert world.accept_trade_offer(monkey, new.id)


def test_stealing_still_records_valuables_and_consumes_food(trade, monkeypatch):
    world, monkey, tourist, valuable, food = trade
    monkeypatch.setattr("random.choice", lambda items: items[0])
    # Existing food theft still fully satisfies hunger.
    assert steal_item(monkey, world, tourist)
    assert monkey.hunger == 0
    assert food not in monkey.held_items
    assert food not in tourist.stolen_valuables
    second = replace(valuable)
    tourist.items.append(second)
    assert steal_item(monkey, world, tourist)
    assert tourist.stolen_valuables[second] == monkey.id
    assert second in monkey.held_items


def test_invalid_theft_does_not_record_owner(trade):
    world, monkey, tourist, valuable, food = trade
    other = replace(valuable)
    tourist.items.append(other)
    tourist.x = 4
    assert not world.transfer_item_to_monkey(monkey, tourist, other)
    assert other in tourist.items
    assert other not in tourist.stolen_valuables
