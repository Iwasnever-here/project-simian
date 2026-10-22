# Project Simian: Progress

## Current Status

Project Simian currently has the foundations of the world simulation, autonomous monkey agents, reproduction and inheritance, social perception, memory, and the first tourist systems.

The current development focus is **brain-controlled monkey-tourist interactions and food/item stealing**. Tourist investigation and interaction actions are now wired into the main neural network, but watching, following and scaring are rarely selected. The next milestone is one verified successful theft in the existing island simulation, without building a separate testing world.

**---**

## World Generation

### Completed

- [x] Procedural island generation

- [x] OpenSimplex noise terrain generation

- [x] Height-based terrain

- [x] Moisture-based environmental variation

- [x] 300 × 300 world

- [x] Multiple terrain types

- [x] Chunk-based world rendering

- [x] 32 × 32 chunks

- [x] Only relevant world chunks rendered by frontend

### Current / Future

- [ ] Further biome balancing

- [ ] Support larger worlds if required

**---**

## World Rendering

### Completed

- [x] React frontend

- [x] TypeScript frontend

- [x] PixiJS world rendering

- [x] Camera panning

- [x] Camera zoom

- [x] Chunk-based rendering

- [x] Monkey rendering

- [x] Tourist rendering

### In Progress / Issues

- [ ] Fix minimap rendering

- [ ] Improve minimap viewport indicator

- [ ] Prevent mouse wheel from scrolling page while zooming world

- [ ] Fix entity popup error

### Future

- [ ] Click minimap to reposition camera

**---**

## Environment

### Completed

- [x] Trees spawn throughout suitable terrain

- [x] Fruit-bearing trees

- [x] Fruit can be consumed by monkeys

- [x] Fruit restores monkey energy

- [x] Fruit respawning

### Needs Work

- [ ] Balance fruit respawn speed

- [ ] Increase meaningful resource scarcity

- [ ] Improve environmental distribution of resources

**---**

## Monkey Agents

### Completed

- [x] Independent monkey agents

- [x] Unique monkey IDs

- [x] Monkey names

- [x] Sex / gender

- [x] Age

- [x] Life stages

- [x] Health

- [x] Energy

- [x] Alive/dead state

- [x] Limited perception

- [x] Movement

- [x] Eating

- [x] Sleeping

- [x] Day/night behaviour

**---**

## Monkey Life Stages

### Completed

- [x] Infant

- [x] Juvenile

- [x] Adult

- [x] Elderly

- [x] Age-based stage calculation

- [x] Age affects vulnerability

- [x] Infants/juveniles prevented from reproducing

- [x] Children mature over time

### Needs Work

- [ ] Fix/verify life stage display in frontend

- [ ] Expand differences in capability between life stages

**---**

## Health and Survival

### Completed

- [x] Health system

- [x] Centralised damage handling

- [x] Centralised healing

- [x] Death when health reaches zero

- [x] Age-based vulnerability

- [x] Starvation/exhaustion can damage health

### Needs Work

- [ ] Fix/verify alive/dead state displayed by frontend

- [ ] Add more causes of death as simulation expands

**---**

## Energy

### Completed

- [x] Energy system

- [x] Movement consumes energy

- [x] Eating restores energy

- [x] Sleeping/resting restores energy

- [x] Low energy affects monkey survival

### Future

- [ ] Further balance energy costs

- [ ] Different movement types/costs

- [ ] Connect energy decisions to danger and competition

**---**

## Day / Night Cycle

### Completed

- [x] Simulation day cycle

- [x] Time-of-day calculation

- [x] Sleeping behaviour

- [x] Sleeping at night is safer than during the day

- [x] Time used by tourist scheduling

### Future

- [ ] Connect predators to day/night cycle

- [ ] Improve time-dependent monkey behaviour

**---**

## Perception

### Completed

- [x] Limited monkey vision

- [x] No global monkey knowledge

- [x] Nearby monkey perception

- [x] Nearby tourist perception

- [x] Vision range system

Current approximate vision range:

```text

VISION_RANGE = 5

```

**---**

## Food Memory

### Completed

- [x] Monkeys can discover food

- [x] Food locations can be remembered

- [x] Monkeys can travel toward remembered food

- [x] A* pathfinding used to reach targets

### Future

- [ ] Make memory quality more strongly affected by the memory trait

- [ ] Forget old/unreliable food locations

- [ ] Handle depleted remembered resources more intelligently

**---**

## Social Memory

### Completed

- [x] `MonkeyMemory`

- [x] `KnownMonkey`

- [x] Monkeys observe nearby monkeys

- [x] Monkey locations stored in memory

- [x] Last-seen tick stored

Current remembered information:

```text

monkey_id

last_x

last_y

last_seen_tick

```

### Future

- [ ] Familiarity

- [ ] Relationships

- [ ] Rivalries

- [ ] Trust

- [ ] Group membership

- [ ] Dominance

**---**

## Tourist Memory

### Completed

- [x] `KnownTourist`

- [x] Monkeys can observe nearby tourists

- [x] Tourist positions can be remembered

- [x] Last-seen tick stored

- [x] Visible tourist items can be stored in memory

Current structure conceptually stores:

```text

tourist_id

last_x

last_y

last_seen_tick

visible_items

```

### Next

- [x] Use selected tourist memory to guide investigation toward a remembered location

- [ ] Use tourist memory to influence longer-term strategy

- [ ] Remember outcomes of tourist interactions

- [ ] Remember successful/failed theft attempts

**---**

## Pathfinding

### Completed

- [x] A* pathfinding

- [x] Monkey pathfinding

- [x] Tourist pathfinding

- [x] Terrain-aware movement

- [x] Failed-path handling

- [x] Path retry cooldown

Current retry concept:

```text

PATH_RETRY_COOLDOWN_TICKS = 20

```

This prevents failed paths from causing expensive A* searches every tick.

**---**

## Monkey Traits

### Completed

Every monkey has:

- [x] Boldness

- [x] Curiosity

- [x] Sociability

- [x] Memory

- [x] Aggression

Traits are approximately:

```text

0.0 → 1.0

```

### Current Behaviour

- [x] Traits vary between monkeys

- [x] Sociability influences social behaviour

- [x] Aggression influences behaviour

- [x] Traits can be inherited

- [x] Traits can mutate

### Needs Work

- [ ] Make aggression produce more noticeable behavioural differences

- [ ] Increase interaction between traits

- [ ] Ensure traits modify decisions rather than directly determining them

**---**

## Reproduction

### Completed

- [x] Adult reproduction

- [x] Compatible partner checking

- [x] Minimum health requirement

- [x] Minimum energy requirement

- [x] Reproduction cooldown

- [x] Parent energy cost

- [x] Child spawning

- [x] Parent IDs stored

- [x] Birth tick stored

- [x] World-controlled pairing prevents duplicate births

Current reproduction requirements include:

```text

MIN_REPRODUCTION_ENERGY = 50

MIN_REPRODUCTION_HEALTH = 50

REPRODUCTION_COOLDOWN_TICKS = 100

```

### Needs Work

- [ ] Continue balancing reproduction frequency

- [ ] Verify long-term population stability

- [ ] Fix population statistics when children are born

**---**

## Genetics

### Completed

- [x] Children inherit traits from parents

- [x] Parent traits averaged

- [x] Random mutation

- [x] Traits clamped to valid range

Current inheritance model:

```text

child_trait =

    average(parent_a_trait, parent_b_trait)

    + mutation

```

Mutation approximately uses:

```text

random.gauss(0, 0.05)

```

### Future

- [ ] Track trait distributions across generations

- [ ] Measure whether environmental pressures create selection

- [ ] Compare survival/reproduction against traits

**---**

## Parenting

### Completed

- [x] Parent relationships stored

- [x] Young monkeys can identify/follow their mother

- [x] Juvenile/infant dependency foundations

### Next

- [ ] Stronger caretaker behaviour

- [ ] Orphan survival penalties

- [ ] Under-50-day monkeys become significantly more vulnerable if mother dies

- [ ] Protection behaviour

- [ ] Possible food assistance

- [ ] Gradual independence with age

**---**

## Social Behaviour

### Completed

- [x] Monkeys observe nearby monkeys

- [x] Basic approach behaviour

- [x] Basic avoidance behaviour

- [x] Basic following behaviour

- [x] Food competition foundations

- [x] Sociability affects behaviour

- [x] Aggression affects behaviour

### Next

- [ ] Relationships

- [ ] Repeated-interaction memory

- [ ] Rivalries

- [ ] Dominance

- [ ] Emergent group formation

**---**

## Groups

### Not Yet Implemented

Planned:

- [ ] Repeated proximity/familiarity

- [ ] Family influence

- [ ] Group formation

- [ ] Group movement

- [ ] Shared areas

- [ ] Food defence

- [ ] Inter-group competition

- [ ] Dominance relationships

Groups should emerge from monkey interactions rather than being randomly assigned.

**---**

## Tourists

### Completed

- [x] Tourist agents

- [x] Tourist spawning

- [x] Boat arrival system

- [x] Tourists travel from boat to temple

- [x] Tourists wander near temple

- [x] Tourists can enter temple

- [x] Tourists spend variable time inside

- [x] Tourists return to boat

- [x] Tourists despawn/leave

- [x] Tourists are invisible while inside temple

- [x] Temple capacity

Current states:

```text

HEADING_TO_TEMPLE

WANDERING_TEMPLE

INSIDE_TEMPLE

HEADING_TO_BOAT

```

Current schedule:

```text

08:00 → tourists arrive

17:00 → tourists return to boat

```

Current temple capacity:

```text

10 tourists

```

**---**

## Tourist Items

### Implemented / Present in Code

- [x] `TouristItem` dataclass with `name`, `value`, `kind`, and optional `hunger_restore`

- [x] Food items (`banana`, `snack`) and valuables (`sunglasses`, `phone`, `camera`, `bag`)

- [x] `generate_tourist_items()` samples 1–3 items from the catalogue

- [x] `Tourist.items` inventory and item names in tourist observation/memory

- [x] Existing item-transfer entry points (`grab_item_monkey`, `grab_tourist_item`) in monkey tourist logic

### Still Needed / Verification

- [ ] Verify `world.transfer_item_to_monkey()` correctly changes both inventories

- [ ] Implement eating stolen food using `hunger_restore`

- [ ] Add a brain-controlled `steal_item` action and distance/item availability mask

- [ ] Dedicated frontend item component

- [ ] Item steal difficulty / success model (later)

- [ ] Ensure generated tourist inventories and food offers support future exchange mechanic

Current item properties:

```python
name: str
value: float
kind: str   # "food" or "valuable"
hunger_restore: float | None = None
```

`steal_score` is not yet part of the item model.

**---**

## Tourist Traits

### Not Yet Implemented

Planned tourist behaviour differences:

- [ ] Generosity

- [ ] Awareness

- [ ] Aggression

- [ ] Caution

These traits should eventually produce behaviours such as:

- Feeding monkeys

- Ignoring monkeys

- Chasing monkeys

- Guarding items

- Becoming frightened

**---**

## Theft

### Mechanic Partially Scaffolded; Not Yet Verified End-to-End

Already present: `grab_tourist_item()` calls `grab_item_monkey()`, which delegates to `world.transfer_item_to_monkey()`. No successful theft has yet been verified in a running test; the main brain does not currently select stealing.

Planned:

- [ ] Monkey can choose `steal_item` when its selected tourist is within range and has possessions

- [ ] Confirm item transfers to monkey and disappears from tourist inventory

- [ ] Consume stolen food and restore hunger

- [ ] Monkey can attempt to steal visible item

- [ ] Item difficulty affects success

- [ ] Monkey traits affect decision/success

- [ ] Tourist traits affect difficulty

- [ ] Successful theft

- [ ] Failed theft

- [ ] Tourist reaction

- [ ] Tourist becomes more cautious after robbery

- [ ] Remaining items become harder to steal

The monkey should not initially know which objects are worth stealing.

**---**

## Tourist Economy

### Not Yet Implemented

Planned:

- [ ] Tourist wants stolen item returned

- [ ] Tourist offers food/resource

- [ ] Different items have different return values

- [ ] Monkey experiences reward

- [ ] Monkey can associate item with previous reward

This will create the core economic loop:

```text

observe tourist

↓

steal item

↓

tourist wants item back

↓

food offered

↓

monkey receives reward

↓

experience remembered

```

**---**

## Neural Learning System

### Implemented

- [x] Per-monkey `MonkeyBrain` neural network, experience replay, Q-based selection and epsilon exploration
- [x] 19-feature state encoding, including selected tourist target status
- [x] Main-brain-controlled survival, social and tourist actions with valid-action filtering
- [x] Curriculum gating (`SURVIVAL_LEARNING_DAYS`, `BASIC_SOCIAL_LEARNING_DAYS`, `TOURIST_LEARNING_DAYS`)
- [x] Tourist actions wired into `Monkey.update()` through `monkey_tourists.py`
- [x] Selected tourist persistence, remembered-position investigation and interaction cooldown
- [x] Tourist visibility/distance masking in `get_valid_actions()` to avoid invisible-target watch/follow/scare attempts
- [x] Survival reward based on hunger, health and energy changes
- [x] Tourist reward parameters wired into `calculate_reward()` and `Monkey.update()` (investigation arrival, interaction success/failure)
- [x] Periodic brain training and profiler instrumentation

Current brain-controlled action vocabulary (check local constants before extending):

```text
wander, seek_food, seek_shelter,
approach_monkey, avoid_monkey, follow_monkey, confront_monkey, socialise,
investigate_tourist, watch_tourist, follow_tourist, scare_tourist, leave_tourist
```

`follow_mother` exists in the overall `MONKEY_ACTIONS` set but is handled primarily through infant logic. `grab_item` / `steal_item` is **not yet a brain-controlled action**.

### Known Limitations

- [ ] Watch/follow/scare are rarely chosen even after investigation is available
- [ ] Rewarded investigation does not guarantee continuation of an encounter: brain chooses afresh each tick
- [ ] Repeated watch/follow successes can farm per-tick rewards; introduce once-per-event/progress signals
- [ ] `scare_tourist` still needs verified tourist reaction integration and reward tied to that outcome
- [ ] Q-learning bootstrap still considers all controlled actions instead of only next-state valid actions
- [ ] Measure action availability vs selection, target arrival and interaction success separately
- [ ] Introduce stealing and food consumption as meaningful survival incentives
- [ ] Consider shared/batched brains later only if profiling justifies it

### Recent Run (day 150)

```text
Population: 243 (185 adults, 44 infants, 14 juveniles)
Deaths in last 25 days: 18 (12 starvation, 6 exhaustion)
Brain action selections in report:
  seek_food            390,899  (73.2%)
  investigate_tourist      667  (0.1%)
  watch_tourist              1
  scare_tourist              7
  leave_tourist            195
  follow_tourist            not listed
World update:          122.445 ms/tick
Monkey updates:        120.424 ms/tick
Per-monkey update:       0.494 ms
Tourists at snapshot:  0 (expected if snapshot is after their daily departure)
```

These are **action-selection counts**, not numbers of successful interactions. The tourist action rates depend on how often selected tourists were visible and actions valid. A different run's death counts or action frequencies alone cannot demonstrate learning improvement.

---

## Predators / Dangers

### Not Yet Implemented

Planned:

- [ ] Wild animals

- [ ] Environment-specific spawning

- [ ] Predator territories

- [ ] Hunting behaviour

- [ ] Day/night activity differences

- [ ] Predator perception

- [ ] Monkey threat perception

- [ ] Monkey escape behaviour

**---**

## Tree Safety

### Not Yet Implemented

Planned:

- [ ] Monkeys can identify safe trees

- [ ] Monkeys flee toward trees

- [ ] Tree climbing

- [ ] Ground predators cannot reach monkey

- [ ] Monkey waits until threat disappears

- [ ] Traits influence flee decisions

**---**

## Simulation Statistics

### Partially Implemented

- [x] Population statistics foundation

- [x] Death tracking

- [x] Birth/reproduction events

### Needs Work

- [x] Fix population count after births

- [x] Current living population

- [ ] Total births

- [x] Total deaths

- [ ] Population over time

- [ ] Age distribution

- [ ] Average trait values

- [ ] Trait distributions

- [ ] Food availability

- [ ] Tourist count

- [ ] Theft statistics

- [ ] Causes of death

- [ ] Generational statistics

**---**

## Entity Inspection

### Monkey Inspection

Implemented/partially implemented:

- [x] Monkey clicking

- [x] Monkey information popup

- [x] Health information

- [x] Traits

- [x] Agent information

Needs work:

- [ ] Fix popup error

- [ ] Verify stage display

- [ ] Verify alive/dead display

- [ ] Display social memory

- [ ] Display tourist memory

### Tourist Inspection

In progress:

- [x] Tourist clicking

- [x] Tourist popup

- [x] Display state

- [x] Display visible possessions

- [ ] Display traits

- [ ] Display robbery state

**---**

## Simulation Controls

### Backend

- [x] Simulation tick loop

- [x] Pause state

- [x] Simulation speed state

Current base tick:

```text

SIMULATION_TICK_SECONDS = 1.0

```

### Frontend / Integration

- [ ] Fix pause controls

- [ ] Fix speed controls

- [ ] Ensure UI remains synchronised with backend

**---**

## Event System

### Completed / Partially Completed

- [x] Simulation event foundations

- [x] Reproduction/birth event

- [x] Event display area

### Future

- [ ] Death events

- [ ] Tourist arrival events

- [ ] Theft events

- [ ] Injury events

- [ ] Group formation events

- [ ] Predator events

**---**

## Performance / Simulation Efficiency

### Profiling Implemented

- [x] World-level performance profiling
- [x] Monkey-update performance profiling
- [x] Separate timings for observation, brain-state construction, inference, action execution, experience finalisation and training

Historical baseline world profile:

```text
world_update: 948.397 ms/tick
monkeys:      940.599 ms/tick
```

Initial monkey profile showed that most time was being spent in repeated brain-state and valid-action observation scans.

### Observation-Reuse Optimisation

Monkey observations are now gathered once before a decision and reused by:

- Brain-state construction
- Valid-action calculation
- Social decision logic
- Tourist decision logic

This reduced the measured world update from approximately:

```text
948 ms/tick
```

to:

```text
704 ms/tick
```

which is roughly a **26% reduction in tick time**.

Current monkey profile after the optimisation:

```text
total:             3.203 ms/monkey-update
observation:       1.308 ms
brain_state:       0.017 ms
brain_inference:   0.242 ms
action_execution:  0.413 ms
training:          0.027 ms
experience:        1.177 ms
```

One remaining performance target is the observation system, especially the repeated post-action observation used to construct the reinforcement-learning `next_state`.

### Performance Targets

- [x] Establish profiler before major architectural rewrites
- [x] Remove redundant pre-action observation scans
- [ ] Profile fruit, monkey and tourist observation separately
- [ ] Reduce expensive tree/resource scans
- [ ] Improve spatial lookup as population/world complexity grows
- [ ] Reuse or cache pathfinding where safe
- [ ] Separate fast simulation stepping from frontend snapshot frequency
- [ ] Add a headless / fast-run mode for long experiments
- [ ] Investigate batched/shared neural inference later

Short-term target:

```text
< 500 ms/tick
```

Strong target:

```text
250–300 ms/tick
```

---

## Infrastructure

### Completed

- [x] Python backend

- [x] FastAPI API

- [x] React frontend

- [x] TypeScript

- [x] PixiJS

- [x] Docker

- [x] Docker Compose

- [x] Frontend and backend containerised together

- [x] CORS configuration

- [x] GZip middleware

Run the project with:

```bash

docker compose up --build

```

**---**

# Current Bugs / Technical Debt

## High Priority

- [ ] Fix entity popup error

- [x] Fix population count when monkeys are born

- [ ] Verify/fix monkey life stage display

- [ ] Verify/fix alive/dead display

- [ ] Fix minimap rendering

- [ ] Fix pause/speed controls

- [ ] Balance fruit respawn

## Lower Priority

- [ ] Prevent page scrolling while zooming map

- [ ] Improve tourist click UI

- [ ] Improve item UI

- [ ] Improve simulation statistics

**---**

# Current Development Focus

The immediate focus is now:

```text
stable monkey ecosystem
↓
efficient observation + simulation loop
↓
expand brain-controlled actions gradually
↓
tourist possessions and generic interactions
↓
tourist reactions and consequences
↓
learned item-taking / exchange strategies
↓
long-run population and behavioural analysis
```

The immediate milestone is:

> **Demonstrate one real item theft from a tourist in the normal island simulation, with inventory transfer, edible-food consumption, and a brain-selectable action.**

Longer-term performance and population stability testing remain important after the mechanic works.

The learning system is already active. The priority is now to make the environment, reward structure and simulation architecture strong enough that additional learned behaviours remain computationally practical and behaviourally meaningful.


---

# Long-Term

Once the tourist economy is functioning:

```text

parenting

↓

relationships

↓

groups

↓

territorial competition

↓

predators

↓

tree safety

↓

generational statistics

↓

learning system

```

The goal is not simply to add more features.

Each system should create **new pressures and choices for the agents**, allowing increasingly complex behaviour to emerge from the interaction between simple systems.