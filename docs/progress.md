# Project Simian: Progress

## Current Status

Last reviewed on **18 November 2026** against the working tree and its automated checks.

The island simulation, reproduction, local perception, memory, neural action selection, tourist theft, and food-for-valuable exchanges are implemented. Monkeys can accept or reject their own visible offers independently of theft cooldown and tourist targeting. Inventory transfer and offer expiry are verified by tests through the normal world-update and decision paths.

The frontend has a responsive PixiJS viewport, minimap, compact top controls, entity inspectors, square image placeholders, held-item displays, pending offers, and event labels for the full trade lifecycle. Population charts cover the current simulation run from day 0 using backend daily snapshots plus a live sample.

The immediate focus is measuring whether normal agents encounter eligible offers and learn to accept useful ones. A successful controlled exchange establishes the mechanic. Natural acceptance rates and improvement against a baseline still need measurement.

### Verification on 18 November 2026

- Backend regression suite passed, **56 tests**.
- Frontend selection regression suite passed, **3 tests**.
- Frontend application TypeScript check and Oxlint passed.
- These checks cover trade validity, exact item identity, repeat acceptance, offer visibility and response dispatch, delayed next-decision learning records, API brain diagnostics, population history, and stale selections.
- Responsive layout and the new markers have passed compilation and a previous production build. Desktop and narrow-screen visual verification remains pending because the previous browser automation check was blocked.
- The dependency environment emits pytest/AnyIO and Starlette/httpx deprecation warnings.

### Review findings still open

1. **P1 — Consistent API snapshots.** `get_tree_states()` iterates the mutable tree dictionary without `world.lock`. Simulation observations and chunk loading can add trees concurrently. `get_monkey_brain_debug()` also reads and evaluates a brain after the entity lookup lock has been released, while training can update its parameters. Guard each complete read or build an immutable snapshot under the lock. The three other brain endpoints and entity detail endpoints already hold the lock. See [API handlers](../backend/api/main.py).

2. **P2 — Diagnostics can perturb experiments.** The brain-choice GET endpoint uses epsilon-greedy selection and consumes the same global Python random stream as simulation behaviour. Brain observation can also generate tree chunks and expire trade offers. Displaying diagnostics can therefore change subsequent stochastic outcomes. Separate diagnostic policy inspection and observation from simulation mutations before claiming repeatable browser-attached experiments. See [brain-choice endpoint](../backend/api/main.py) and [learning helpers](../backend/simulation/agents/monkey/monkey_learning.py).

3. **P2 — Sleeping transitions span multiple ticks.** Pending rewards accumulate while a monkey sleeps and the transition closes at its next decision. The replay record has no duration and the target applies `GAMMA` once. Define whether discounting is per decision or per simulation tick. Per-tick discounting requires elapsed duration and appropriately discounted rewards. See [experience model](../backend/simulation/agents/experience.py) and [training](../backend/simulation/agents/monkey/monkey_learning.py).

4. **P2 — Sparse trades and reward balance.** Tours require a stolen valuable, the original owner, affordable food, proximity, and time before departure. Stolen food currently clears all hunger, while exchanged food uses its own `hunger_restore`. Some tourist interactions also receive repeatable action bonuses. Measure opportunities and outcomes before changing these incentives.

5. **P2 — Reporting and replay limits.** The event buffer keeps only 100 events, so counting retained events does not give full-run trade totals. Population history grows one entry per day and is returned in full on each status poll. Worlds, history, model parameters, and replay buffers reset with the backend process. Run-level metrics, persistence, and long-run history transfer costs remain open.

6. **P3 — Legacy helpers and timer conventions.** `finalize_tourist_experience()` still calls an absent `_get_tourist_state()` and constructs `Experience` without required `done`. The active path uses `finalize_brain_experience()`. Tourist temple deadlines still use day-local `tick`, while trade expiry uses `total_tick`. Current 17:00 departure limits midnight exposure, but the timer convention needs alignment before extending visits overnight.

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

### Implemented

- [x] React, TypeScript, and PixiJS rendering.
- [x] Visible chunk loading and disposal of distant terrain textures.
- [x] Pan, cursor-centred wheel zoom, and entity selection.
- [x] Renderer dimensions and hit area follow the map panel through `ResizeObserver`.
- [x] Camera centre is retained when the panel changes size.
- [x] Minimap thumbnail and current viewport rectangle.
- [x] Removed minimap heading and placed zoom information over the viewport.
- [x] Detailed monkey faces/tails and tourist clothing/hats.
- [x] Compact top pause, speed, and spawn controls.
- [x] Wheel zoom prevents page scrolling and map pointer cancellation clears dragging.

### Verification / Future

- [ ] Complete visual QA at desktop, tablet, and narrow-screen widths.
- [ ] Click minimap to reposition camera.
- [ ] Replace image placeholders with assets when supplied.

**---**

## Environment

### Completed

- [x] Trees spawn throughout suitable terrain

- [x] Fruit-bearing trees

- [x] Fruit can be consumed by monkeys

- [x] Fruit reduces hunger through `Monkey.eat()`; sleeping restores energy

- [x] Fruit respawning

### Needs Work

- [x] Balance fruit respawn speed

- [x] Increase meaningful resource scarcity

- [x] Improve environmental distribution of resources

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

- [x] Fix/verify life stage display in frontend

- [x] Expand differences in capability between life stages

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

- [x] Fix/verify alive/dead state displayed by frontend

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

- [x] Further balance energy costs

- [x] Different movement types/costs

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

- [x] Forget old/unreliable food locations

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

- [x] Continue balancing reproduction frequency

- [x] Verify long-term population stability

- [x] Fix population statistics when children are born

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

- [x] Stronger caretaker behaviour

- [x] Orphan survival penalties

- [x] Under-50-day monkeys become significantly more vulnerable if mother dies

- [ ] Protection behaviour

- [x] Possible food assistance

- [x] Gradual independence with age

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

### Implemented

- [x] `TouristItem` stores name, value, kind, and optional hunger restoration.
- [x] Catalogue food and valuables are copied into distinct inventory instances.
- [x] Tourist observations remember visible item names.
- [x] Ownership transfer removes the exact item from the tourist and adds it to the monkey.
- [x] Stolen valuables record their original tourist and thief.
- [x] Shared inventory UI displays held monkey items and tourist possessions with square image placeholders.
- [x] Item value bounds the food a tourist can offer.
- [x] Acceptance returns the exact stolen valuable and consumes the exact offered food once.

### Still needed

- [ ] Item-specific theft difficulty and consequences.
- [ ] Persistent item IDs for saved worlds or external commands. Current ownership uses in-memory object identity.
- [ ] Measure the availability of suitable tourist food.
- [ ] Reconcile food-theft hunger restoration with trading and resource balance.

Current food theft fully satisfies hunger when an edible item is taken. Acceptance restores only `offer.food.hunger_restore`. The earlier claim that both routes use that amount was inaccurate.

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

### Implemented and verified

- [x] `steal_item` is a brain-controlled action.
- [x] Valid-action checks require the selected tourist, proximity, possessions, and theft cooldown eligibility.
- [x] Successful theft transfers one exact item and logs `tourist_theft`.
- [x] Food is consumed immediately and valuables remain in the monkey inventory.
- [x] Theft clears the tourist target and starts the interaction cooldown.
- [x] Automated tests cover transfer validity and event emission.
- [x] Earlier ordinary simulation observations recorded successful food and valuable thefts.
- [x] Forced theft preference is opt-in through `SIMIAN_DEBUG_FAVOUR_STEALING` and defaults off.

### Remaining

- [ ] Probabilistic theft difficulty and guarding reactions.
- [ ] Item- and tourist-specific risk.
- [ ] Measure availability, attempts, success, and resulting offers separately.
- [ ] Demonstrate a learned item-taking/exchange strategy against a baseline.

Tourists can flee a monkey that is scaring them. Additional caution after theft and progressively harder repeat thefts are planned.

**---**

## Tourist Economy

### Implemented and verified

- [x] Tourists find visible thieves still holding their stolen valuables.
- [x] They prioritise the most valuable eligible stolen possession.
- [x] An offer uses one actual food item, choosing the highest value that does not exceed the stolen item's value. Ties prefer higher hunger restoration.
- [x] One pending offer per monkey and tourist, with a 30-`total_tick` lifetime.
- [x] Tourists wait while an offer is pending and retry after a 30-tick cooldown when it closes.
- [x] Fleeing, temple entry, departure, loss of proximity, missing inventory, death, and removal invalidate offers.
- [x] Monkeys perceive only their own valid offer from a visible nearby tourist.
- [x] `accept_trade` and `reject_trade` become eligible with tourist actions at day 45.
- [x] Offer response uses its ID and is independent of theft cooldown and `target_tourist_id`.
- [x] Acceptance revalidates and returns the exact valuable, consumes food, and applies hunger restoration.
- [x] Rejection preserves both inventories. Repeat acceptance cannot transfer or feed twice.
- [x] Both inspectors display offer participants, requested item, food, and remaining ticks.
- [x] Offered, accepted, rejected, expired, and cancelled lifecycle events.

### Observations and next milestone

Earlier investigation in this project chat ran seeds 7, 19, and 31 for days 45–47 with fresh brains and normal island updates. Across 450 tourists, 146 had an affordable food/valuable pair at first observation. There were one food theft, one valuable theft, and zero offers. This is a short opportunity sample, not a trained-policy evaluation.

A separate earlier live API observation at day 64 recorded seven thefts and zero offers. Four thefts were food and two of the three valuables were stolen at or after 17:00. The retained events did not establish why the remaining theft produced no offer. These observations were not rerun during the 18 November review.

- [ ] Record full-run eligibility, offer, response, and cancellation counts.
- [ ] Compare a simple baseline and the learned policy using matched seeds.
- [ ] Measure acceptance per eligible offer, hunger benefit, survival, and opportunity frequency.
- [ ] Demonstrate a naturally completed exchange in a repeatable run.
- [ ] Counteroffers, increasing offers, food bundles, and tourist-specific bargaining traits remain future work.

**---**

## Neural Learning System

### Implemented

- [x] Per-monkey network with **21 inputs → 32 → 32 → 17 action scores**.
- [x] Sixteen brain-controlled actions; the wider action list also contains `follow_mother`, handled by infant rules.
- [x] The state includes selected-target status, offer presence, and offered hunger benefit.
- [x] Survival, social, theft, and accept/reject trade dispatch.
- [x] Curriculum stages at days 25, 35, and 45.
- [x] Epsilon-greedy exploration with `EPSILON = 0.1`.
- [x] Replay limited to 1,000 experiences, batch size 32, and staggered training every 100 ticks.
- [x] Adam at 0.001, `GAMMA = 0.95`, MSE loss, and gradient clipping.
- [x] Experience includes next-state valid actions, used to mask bootstrapping targets.
- [x] A transition closes at the next actual decision using its already-gathered observations, so intervening tourist offers enter the next state.
- [x] Rewards accumulate while an action remains pending, including sleeping ticks. Death finalises a terminal transition.
- [x] Brain-state, output, choice, and debug endpoints have success and missing-monkey smoke coverage.

### Remaining limitations

- [ ] Resolve variable-duration discount semantics for sleep-spanning transitions.
- [ ] Quantify repeated tourist-action reward incentives and sparse exchange opportunities.
- [ ] Include enough item/outcome context to support longer-term value comparisons if experiments justify it.
- [ ] Compare policies with controlled seeds. Lower training loss or action counts alone do not demonstrate improved behaviour.
- [ ] Separate target network, shared policies, batched inference, and saved models are future experiments.

The current online network supplies both current predictions and detached bootstrap estimates.

### Historical run (day 150, recorded before this review)

The earlier report recorded population 243, 18 deaths in its last 25 days, and 122.445 ms per world tick. It predates the latest trade, transition, and chart changes. It is not a new performance result or a controlled comparison. The earlier action totals represented choices rather than successful interactions.

**---**

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

### Implemented

- [x] Living population, total monkeys created, and derived deaths.
- [x] Day-0 snapshot, one saved population sample per simulation day, and a live sample in `/simulation/status`.
- [x] Alive, Deaths, and Born chart views span the current backend run and survive browser refresh.
- [x] Console demographic reports include life stages, reproduction readiness, interval births, and death causes.
- [x] Console profiles include tree and tourist counts and action-selection frequencies.
- [x] Event records identify thefts and each trade lifecycle outcome.

### Remaining

- [ ] Relabel “Total Born” or expose natural births separately. Current total includes initial monkeys and manual spawns.
- [ ] Full-run trade counters or event export beyond the latest 100 events.
- [ ] Age/trait distributions and food availability in the UI.
- [ ] Persistent history and model checkpoints across backend restarts.
- [ ] Generational statistics, trait-change analysis, and reproducible experiment output.
- [ ] Measure history response size and chart cost during long runs.

Daily sampling describes long-term trends; it does not preserve every intraday population change.

**---**

## Entity Inspection

### Implemented

- [x] Monkey/tourist selection and details.
- [x] Monkey condition, traits, age, life stage, alive status, behaviour, and position.
- [x] Held monkey items and tourist inventory.
- [x] Pending trade offer on both participant endpoints, with remaining simulation ticks.
- [x] Shared item rows and square portrait/item placeholders.
- [x] Aborted requests, URL-specific results, and 404 clearing prevent stale selections.

### Remaining

- [ ] Desktop/narrow-screen visual verification and supplied artwork.
- [ ] Social and tourist memory inspection.
- [ ] Tourist traits and deeper robbery history when those systems exist.
- [ ] Richer tourist behaviour/destination details in the inspector.

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

- [x] Fix pause controls

- [x] Fix speed controls

- [x] Ensure UI remains synchronised with backend

**---**

## Event System

### Implemented

- [x] Birth events and a live feed/news ticker.
- [x] Successful theft events for food and valuables.
- [x] Trade offered, accepted, rejected, expired, and cancelled events.
- [x] Events carry IDs, simulation day/tick, and participant/item data.
- [x] Invalid/repeated acceptance cannot emit an additional accepted event.
- [x] The latest 100 events are available through `/events`.

### Remaining

- [ ] Durable full-run event export and aggregated metrics.
- [ ] Death, arrival, injury, group, and predator events when their logging or systems are added.

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

Historical monkey profile after the observation-reuse optimisation:

```text
total:             3.203 ms/monkey-update
observation:       1.308 ms
brain_state:       0.017 ms
brain_inference:   0.242 ms
action_execution:  0.413 ms
training:          0.027 ms
experience:        1.177 ms
```

Experience finalisation now reuses the next decision observation. Reprofile the current code before choosing the next optimisation. Nearby monkey visibility still scans the population, and shelter lookup still scans loaded trees.

### Performance Targets

- [x] Establish profiler before major architectural rewrites
- [x] Remove redundant pre-action observation scans
- [x] Separate fruit, monkey, and tourist observation timers
- [x] Reduce expensive tree/resource scans
- [x] Improve spatial lookup as population/world complexity grows
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

- [ ] Guard complete tree/brain-debug API snapshots with the world lock.
- [ ] Make diagnostic observations and action inspection safe for reproducible experiments.
- [ ] Resolve sleep-spanning transition discount semantics.
- [ ] Measure trade opportunities and policy outcomes with matched seeds.
- [ ] Validate resource balance and generation survival with repeatable long runs.
- [x] Entity popup, population count updates, alive serialization, and stale selection fixes.
- [x] Responsive viewport, minimap placement, wheel handling, and top controls implemented.
- [ ] Complete their visual/interaction QA at supported viewport sizes.

## Lower Priority

- [ ] Supply image assets for item and portrait placeholders.
- [ ] Extend social/tourist memory inspection.
- [ ] Distinguish created monkeys from natural births in UI labels.
- [ ] Add persistent run statistics and remove broken legacy tourist-experience scaffolding.
- [ ] Standardise tourist deadlines on monotonic simulation time before supporting overnight visits.

**---**

# Current Development Focus

1. Validate opportunity generation for trading during ordinary island runs.
2. Collect full-run metrics and compare learned and baseline policies across matched seeds.
3. Address the API snapshot, diagnostic reproducibility, and learning-duration issues recorded above.
4. Complete frontend visual verification.
5. Reprofile after these correctness checks, then consider spatial indexing or batched inference if measurements justify them.

The next behavioural milestone is a naturally completed, reproducible valuable-for-food exchange, with eligibility, offer, response, and outcome visible in the metrics.

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