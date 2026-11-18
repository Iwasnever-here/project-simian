# Project Simian: Design Document

Last reviewed on **18 November 2026**. Implemented decisions below reflect the current working tree. Future systems remain proposals. Detailed checks and unresolved review findings are tracked in [progress.md](progress.md).

## Current decisions

| Decision in use | Reason and consequence |
| --- | --- |
| The Python world owns behaviour and inventory mutations. React/PixiJS consumes snapshots. | Decision policy, execution rules, and rendering remain independently inspectable. The current API process owns one in-memory world. |
| Use a world `threading.RLock` around simulation updates and complete snapshot/transaction operations. | Nested world methods can acquire the same lock. The review found incomplete locking in the tree and brain-debug handlers that still needs correction. |
| Each monkey has its own 21-input, 32/32-hidden-layer Q network and replay buffer. | Simple independent learning with limited local observations. Rare experiences are fragmented across agents. Shared/batched policies remain future experiments. |
| Restrict both action selection and bootstrap targets to valid actions. | An unavailable trade or interaction must not inflate the value of a transition. Replay stores the next-action mask. |
| Close a learning transition at the next actual decision. | The next state includes intervening tourist offers and other agent updates. Reuse those observations and finalise deaths terminally. Sleeping can span several ticks, so discount-per-tick versus discount-per-decision semantics still needs a decision. |
| Start with a single valuable exchanged for a single actual food item. | Preserve exact ownership and a small transaction surface. The tourist chooses the highest-value food within the stolen item's value budget. Its offer-generation policy is deterministic given the eligible inventory. |
| Address offer responses by offer ID independently of tourist target and theft cooldown. | Theft clears targeting, but the monkey must still be able to respond to a visible incoming offer. Acceptance revalidates before moving the exact items. |
| Offer lifetime and retry cooldown are both 30 simulation ticks. | Uses monotonic `total_tick`. Proximity, participants, inventories, fleeing, temple status, and departure can close offers early. |
| Keep population history in the backend from day 0, with daily snapshots plus a current API sample. | Full-run trends survive a browser refresh. Data resets with the backend and the complete history is currently sent on each status poll. |
| Resize the Pixi renderer to its panel and use its measured dimensions for interactions. | Viewport bounds, chunk requests, hit testing, and minimap coordinates follow screen size. Preserve the camera centre and dispose distant textures. |
| Keep the latest 100 events for the feed. | Suitable for current activity. Experiment totals need separate run counters or export. |
| Disable forced theft preference by default. | `SIMIAN_DEBUG_FAVOUR_STEALING` is an explicit mechanic-testing switch. Evaluation must record its setting. |

These choices support tested mechanics. Existing checks verify transactions and learning records. Ordinary-run acceptance rates and baseline comparisons remain open.

Future ideas retained from the original notes include additional monkey conflict, night predators, and tourists taking items. They are outside the implemented scope.


## Core Idea

****Project Simian**** is an agent-based simulation exploring whether complex social and economic behaviour can emerge from relatively simple individual rules.

The simulation takes place on a procedurally generated island inhabited by autonomous monkeys. Monkeys have limited perception, memory, physical needs, behavioural traits and inherited characteristics.

Tourists, a temple and tourist possessions are now part of the simulation. The long-term goal is to let monkeys learn whether behaviours such as stealing valuable objects, exchanging stolen items for food, competing over profitable locations and developing group strategies are useful without directly scripting those outcomes.

**---**

## 1. World Generation

### Terrain

The island is procedurally generated using ****OpenSimplex noise****.

Generate multiple noise maps:

#### Height Map

Controls the basic terrain:

- Deep water

- Shallow water

- Sand

- Grass

- Mountains / high ground

#### Moisture Map

Combined with height to produce different environments:

- Dry grassland

- Forest

- Dense forest

- Wet areas

- Rocky areas

This prevents the island from simply being concentric bands of terrain based on height.

### World Size

Current world:

```text

300 × 300 tiles

```

The simulation should support larger worlds later without requiring the entire map to be rendered at once.

**---**

## 2. World Rendering

### Chunk Loading

Divide the world into:

```text

32 × 32 tile chunks

```

Only render chunks visible within or close to the player's viewport.

The ****simulation itself continues across the whole world****. Chunking is a rendering optimisation, not a simulation boundary.

### Camera

The player can:

- Pan around the world

- Zoom in and out

- Click monkeys

- Click tourists

- Inspect entities without affecting the simulation

The mouse wheel zooms over the map through a non-passive wheel listener. Renderer resizing uses the panel dimensions, and the camera preserves the viewed centre. The map has no fixed 900 × 600 requirement. Minimap text has been removed and zoom appears within the map. Desktop and narrow-screen visual verification remains pending.

### Minimap

Display a small minimap showing:

- Entire island

- Simplified terrain

- Current camera position

- Camera viewport rectangle

Potential later feature:

- Click minimap to move camera

**---**

## 3. Environment and Resources

### Trees

Trees spawn according to suitable terrain/environment conditions.

Some trees produce fruit.

Different areas of the island therefore naturally contain different amounts of food.

### Fruit

Fruit acts as one of the monkeys' primary food sources.

Fruit should:

- Reduce hunger

- Respawn over time

- Exist at specific locations

- Become depleted when eaten

Respawn rates should be slow enough that monkeys actually need to search and compete rather than camping beside an infinite food source.

**---**

## 4. Monkey Agents

Every monkey is an independent agent.

A monkey does ****not**** have global knowledge of the simulation.

It only knows:

- What it can currently perceive

- What it remembers

- Innate information it is explicitly designed to know

This prevents "god vision."

### Identity

Each monkey has:

- Unique ID

- Name

- Sex / gender

- Age

- Life stage

- Position

- Parents

- Health

- Energy

- Alive/dead state

**---**

## 5. Life Stages

Monkeys progress through:

```text
Infant
Juvenile
Adult
Elderly
```

Age affects capability, independence and reproductive eligibility.

### Infants

- Highly vulnerable
- Dependent on their mother/caretaker
- Cannot reproduce
- Currently bypass the neural brain and follow their mother as a hard behavioural rule
- While their mother is alive, infant hunger is temporarily sustained rather than forcing infants to seek food independently

### Juveniles

- More independent than infants
- Cannot reproduce
- Use the normal learned behaviour pathway rather than being permanently locked into following their mother
- Must be able to seek food and shelter for themselves so they can survive to adulthood

### Adults

- Highest general survival ability
- Can reproduce when health, energy, distance and cooldown requirements are met
- Use the learned behaviour system

### Elderly

- Increased physical vulnerability
- Cannot reproduce under the current adult-only reproduction rule
- Can retain advantages from accumulated experience and memory

Older monkeys can therefore become physically weaker while potentially being behaviourally more experienced.

## 6. Health and Survival

Monkeys have:

```text

0–100 health

```

At:

```text

health <= 0

```

the monkey dies.

Health can be affected by:

- Starvation

- Exhaustion

- Age

- Animals

- Competition

- Future tourist interactions

Young and elderly monkeys should generally be at greater risk than healthy adults.

**---**

## 7. Energy

Actions consume different amounts of energy.

For example:

```text

Running / long movement → high cost

Walking → moderate cost

Staying still → low cost

Sleeping → recovery

Eating → energy gain

```

Movement therefore has an actual survival cost.

A monkey shouldn't constantly pathfind across the island simply because food exists somewhere.

**---**

## 8. Day and Night

The simulation contains a continuous day/night cycle.

Time influences behaviour.

### Sleeping

Monkeys need sleep.

Sleeping during the night should generally be safer than sleeping during the day.

However, staying still should not automatically mean being safe.

A sleeping or stationary monkey may still be vulnerable to predators or other threats.

This makes ****where and when a monkey rests**** meaningful.

**---**

## 9. Perception

Monkeys have limited vision.

Current vision range:

```text

VISION_RANGE = 5

```

Monkeys can perceive nearby:

- Other monkeys

- Tourists

- Food

- Threats

- Environmental features

Anything outside perception must come from memory rather than direct knowledge.

**---**

## 10. Memory

Monkeys maintain their own internal memory.

### Food Memory

A monkey can remember previously discovered food locations.

Instead of:

```text

Find closest fruit anywhere in world

```

behaviour should resemble:

```text

See fruit

↓

Remember location

↓

Become hungry later

↓

Recall promising food location

↓

Travel there

```

The monkey can use ****A\\***** to navigate toward remembered resources.

Memory should eventually be imperfect.

The `memory` trait can influence:

- How long locations remain remembered

- How accurately locations are remembered

- How many locations can be retained

### Social Memory

Monkeys remember other monkeys they have encountered.

Stored information includes:

```text

monkey_id

last_x

last_y

last_seen_tick

```

This can eventually support:

- Relationships

- Rivalries

- Group formation

- Recognising competitors

- Remembering family

### Tourist Memory

Monkeys can also remember tourists they have observed.

```text

tourist_id

last_x

last_y

last_seen_tick

visible_items

```

This becomes particularly important once stealing behaviour exists.

**---**

## 11. Pathfinding

Monkeys and tourists use ****A\\***** pathfinding.

Pathfinding should account for:

- Impassable terrain

- Terrain boundaries

- Destination

- Failed routes

Failed pathfinding should not trigger another expensive A\\* search every simulation tick.

A retry cooldown can be used before attempting the route again.

**---**

## 12. Behavioural Traits

Each monkey has inheritable behavioural traits between:

```text

0.0 → 1.0

```

Current traits:

### Boldness

Influences willingness to approach danger, tourists or contested resources.

### Curiosity

Influences exploration and investigation of unfamiliar things.

### Sociability

Influences attraction toward other monkeys and potential group behaviour.

### Memory

Influences memory effectiveness.

### Aggression

Influences willingness to challenge competitors or defend resources.

Traits should modify probabilities and decisions rather than directly dictate behaviour.

An aggressive monkey should not automatically attack everything. Aggression should make aggressive choices more likely under appropriate circumstances.

**---**

## 13. Reproduction

Adult monkeys can reproduce when conditions allow.

Requirements include:

- Compatible adult partner

- Minimum health

- Minimum energy

- Reproduction cooldown completed

Reproduction pairing should be controlled by the ****World/simulation layer**** rather than letting both monkeys independently spawn offspring.

This avoids:

```text

A reproduces with B

B reproduces with A

```

creating two accidental children.

### Parent Data

Children remember their parents:

```text

parent_ids

birth_tick

```

Parents track reproduction cooldowns.

Reproduction also costs energy.

**---**

## 14. Genetics

Children inherit behavioural traits from their parents.

Basic inheritance:

```text

parent A trait

        +

parent B trait

        ↓

average

        ↓

small mutation

        ↓

child trait

```

Mutation allows traits to diverge between generations.

This creates the foundation for population-level behavioural change without requiring a full Mendelian genetics simulation.

Inheritance and mutation alone are not enough to demonstrate evolution. Selection needs to emerge across generations.

**---**

## 15. Parenting

Young monkeys depend on adults, but the dependency should change as they mature.

### Current Infant Rule

Infants currently follow their mother/caretaker as a hard behavioural rule rather than asking the neural network to choose between unrelated actions.

```text
Infant
  ↓
Follow mother
  ↓
Remain dependent during early life
  ↓
Juvenile
  ↓
Enter normal learned behaviour pathway
```

While an infant's mother is alive, infant hunger is currently held stable as a temporary simplification. If the mother dies, hunger begins increasing normally again.

This avoids forcing infants to independently solve food-seeking before a more complete parenting/feeding system exists.

### Juveniles

Juveniles should not be permanently forced into the mother-follow path. They need access to normal behaviour such as food seeking and shelter seeking so that offspring can realistically survive to adulthood.

### Future Parenting Expansion

The system can later expand into:

- Protection
- Food assistance
- Learning through observation
- Social learning
- Separation as offspring mature
- Caregiver choice beyond biological mothers

### Orphan Survival

Do not simply kill an infant when its mother dies.

Instead remove the advantages provided by parenting and allow the resulting survival pressure to emerge naturally.

This creates an emergent consequence rather than:

```text
mother_dead = infant_dead
```

## 16. Social Behaviour

Monkeys perceive nearby monkeys and react differently depending on their traits and circumstances.

Possible interactions:

- Approach

- Avoid

- Follow

- Compete

- Ignore

Sociability, aggression, hunger, age and relationships should all contribute to these decisions.

**---**

## 17. Groups

A major future system is spontaneous group formation.

Groups should ideally ****emerge from repeated interactions****, rather than monkeys being randomly assigned to teams.

Possible causes:

- Family relationships

- Repeated proximity

- Shared food locations

- Protection

- Similar movement patterns

- Mutual tolerance

Eventually groups may:

- Travel together

- Share territory

- Defend food

- Compete with other groups

- Develop dominance relationships

Avoid hard-coding the result being investigated.

For example, automatically creating a troop whenever five monkeys stand together would manufacture group formation rather than allowing it to emerge.

**---**

## 18. Resource Competition

Food should be limited enough that monkeys occasionally compete.

Competition may depend on:

```text

hunger

aggression

boldness

social relationships

group size

health

age

```

Possible outcomes:

- Retreat

- Share/tolerate

- Threaten

- Fight

- Steal food

Competition also creates selection pressure that can make inherited behavioural differences meaningful.

**---**

## 19. Tourists

Tourists arrive on the island by boat.

Their existence introduces an entirely new resource system for the monkeys.

### Tourist Schedule

```text

08:00

Boat arrives

↓

Tourists leave boat

↓

Travel toward temple

↓

Explore / enter temple

↓

Spend day around temple

↓

17:00

Return to boat

↓

Leave island

```

Tourists know the temple and boat locations.

**---**

## 20. Temple

The temple acts as the main tourist destination.

Tourists can:

- Walk toward it

- Wander nearby

- Enter it

- Spend a random period inside

- Leave again

Current states:

```text

HEADING_TO_TEMPLE

WANDERING_TEMPLE

INSIDE_TEMPLE

HEADING_TO_BOAT

```

The temple has limited capacity.

Current target:

```text

10 tourists

```

Tourists inside the temple are not visible to monkeys.

This prevents monkeys from magically tracking tourists through walls.

**---**

## 21. Tourist Items

Tourists carry visible items.

Potential items:

```text

Phone

Camera

Sunglasses

Hat

Food

Bag

Bottle

```

Each item has at least two important properties.

### Steal Difficulty

```text

steal_score

```

Represents how difficult or risky the item is to steal.

### Return Value

```text

value

```

Represents how much food or another resource the tourist is willing to exchange to recover it.

This creates a risk/reward problem:

```text

easy item + low value

vs

difficult item + high value

```

**---**

## 22. Tourist Behavioural Traits

Tourists should differ from one another.

Potential behaviours:

- Feed monkeys

- Ignore monkeys

- Chase monkeys

- Guard possessions carefully

- Become frightened

- Be highly observant

Eventually these should preferably become continuous traits rather than rigid character classes.

For example:

```text

generosity

awareness

aggression

caution

```

These can combine to create different tourist personalities.

**---**

## 23. Robbery / Theft

The current brain-controlled `steal_item` action transfers one possession from the selected visible tourist within interaction range. Valuables remain held and retain exact original-owner/thief tracking. Food is immediately consumed. A successful transfer emits a theft event.

Theft starts an interaction cooldown and clears the ordinary tourist target. Incoming trade responses bypass that targeting requirement. Difficulty, guarding, and increasing caution after theft remain planned.

### Current tourist response and trading

1. The tourist finds a visible nearby monkey still holding one of its stolen valuables.
2. It prioritises its highest-value eligible valuable and selects the highest-value real food item with positive finite value no greater than that valuable. Food must have positive finite hunger restoration.
3. The world creates one pending offer per participant, valid for 30 `total_tick` ticks.
4. The tourist pauses normal movement while waiting. Rejection, acceptance, expiry, or cancellation starts a 30-tick retry cooldown.
5. The monkey can accept, reject, or ignore the offer after tourist actions unlock at day 45.
6. Acceptance holds the world lock, verifies the original participants, ownership, distance, food, and lifetime, consumes the offer, returns the exact valuable, consumes food, and restores hunger once.
7. The world logs offered, accepted, rejected, expired, and cancelled outcomes.

Fleeing and departure retain priority. Trading closes at 17:00 and invalid participants, temple status, or lost proximity cancel offers.

The current transfer rule for stolen food clears all hunger. Exchanged food restores only its `hunger_restore`. This balance difference is recorded for evaluation.

Counteroffers, changing prices after rejection, food bundles, tourist generosity/awareness traits, and persistent item IDs are future work.

**---**

## 24. Current Learning System

Each monkey owns a feed-forward network with **21 inputs, two 32-unit ReLU hidden layers, and 17 output scores**. Sixteen actions belong to the controlled policy. The wider list also includes `follow_mother`, principally executed through infant dependency rules.

### Observation and available actions

The input contains hunger, energy, health, five traits, maturity, day/night, food/monkey/tourist visibility and distances, tourist possessions, held-item state, tourist target status, pending-offer availability, and offered hunger benefit.

Brain-controlled actions include survival, social interactions, tourist investigation/watch/follow/scare/leave, theft, and trade acceptance/rejection. Curriculum filtering introduces basic social actions at day 25, further social actions at day 35, and tourist actions at day 45. Infant following and urgent-food continuation include explicit rules.

Only valid actions can be selected. Offer responses require the monkey's own valid visible offer and use its ID, independently of ordinary targeting and theft cooldown.

### Reward and experience boundaries

Hunger reduction is weighted by previous hunger, with health and energy deltas contributing to survival reward. Tourist investigation arrival and successful interactions also have small trait-weighted bonuses, including theft. Invalid interactions receive a penalty. The repeated tourist bonuses and food restoration differences need experiment-driven assessment.

The active replay record contains state, action, accumulated reward, next state, terminal flag, and next-valid-action indices. A transition closes immediately before the next normal policy decision using its current observation, after other world agents have updated between turns. Pending rewards accumulate through sleeping ticks, and death closes the transition terminally.

The present implementation treats each decision transition with one discount factor regardless of how many sleeping ticks it spans. Review the intended temporal objective before introducing more long-duration actions.

### Training

- Epsilon-greedy exploration with epsilon 0.1.
- At most 1,000 replay experiences per monkey, with random batches of 32.
- Training every 100 ticks, staggered by monkey ID.
- Adam optimiser at learning rate 0.001, MSE loss, and gradient clipping at norm 1.
- Nonterminal target of reward plus `0.95 × max Q(next_state, valid_next_action)`.
- Terminal and empty-mask experiences use reward only.
- Current and detached bootstrap Q-values both come from the online network.

A separate target network, shared policy, batched training, persistent checkpoints, and learned item-specific valuations remain experiments.

### Evidence standard

Automated tests establish state dimensions, curriculum masks, next-decision timing, execution, transaction invariants, and finite optimisation steps. Earlier short normal-island samples produced sparse thefts and zero offers. Repeatable ordinary-run exchanges and policy improvement still require full-run opportunity metrics and matched-seed baseline comparisons.

The inactive legacy `finalize_tourist_experience()` scaffolding is incompatible with the current `Experience` constructor and needs review before reuse.

**---**

## 25. Dangers and Predators

Wild animals can inhabit particular parts of the island.

Predators may:

- Spawn in specific environments

- Have territories

- Hunt monkeys

- Become more active at particular times

- Have different sensory capabilities

Predator-specific sensory behaviour should be preferred over one global rule.

For example, a nocturnal predator might have better relative vision at night while monkeys become less capable of detecting it.

This creates an actual reason for monkeys to seek safety at night.

**---**

## 26. Trees as Safety

Trees should eventually become more than food sources.

Monkeys may be able to climb trees to escape ground predators.

Possible behaviour:

```text

Detect threat

↓

Evaluate distance/danger

↓

Locate remembered/visible safe tree

↓

Run toward tree

↓

Climb

↓

Wait until danger passes

```

Boldness, age, energy and previous experience could influence when a monkey chooses to flee.

**---**

## 27. Simulation Statistics

The backend records population at day 0 and at the end of each day-boundary update. `/simulation/status` returns these points plus a fresh current sample, avoiding a duplicate sample at the same tick.

The frontend Alive, Deaths, and Born graph views cover the whole backend run using simulation ticks and day labels. Browser refresh retrieves the existing history. Backend restart resets the world, history, model parameters, and replay buffers.

`total_monkeys_created` includes initial agents and manual spawns. The “Total Born” label therefore needs clarification or a separate natural-birth count. Deaths are derived from total created minus the living population.

Console demographic output provides stage counts, adult genders, reproductive eligibility, interval births, and death causes. Trait distributions, food-availability charts, and generational comparisons remain future UI/analysis work.

Trade experiments need opportunity counts, offers, responses, cancellation reasons, hunger effects, and survival outcomes. The latest-100-event feed cannot supply durable full-run totals. Daily history also needs response-size and rendering-cost measurement for very long runs.

**---**

## 28. Entity Inspection UI

The monkey inspector displays identity, life stage, condition, traits, behaviour, position, held items, and any pending trade offer. Tourist inspection displays identity, position, possessions, and a pending offer.

Both views use shared inventory rows and square image placeholders. Pending offers identify the monkey and tourist, the requested valuable, the food offered, and remaining simulation ticks.

Requests are aborted on selection changes, results are associated with the requested URL, and a 404 clears a removed entity. Offer summary reads hold the world lock and do not expire or create offers.

Social/tourist memory detail, richer tourist behaviour/destination display, relationship history, and supplied image assets remain future additions. Layout verification at desktop and narrow widths remains outstanding.

**---**

## 29. Simulation Controls

The compact top control strip provides pause/resume, 1×/8×/32×/64× speed selection, and manual monkey spawn. The header also shows simulation day and time. Map controls provide pan and wheel zoom.

The backend tracks pause and speed separately from the world and advances one awaited update at a time using `asyncio.to_thread`. The loop sleeps for `1.0 / speed` seconds after computation. Effective tick rate includes computation time, so requested speed is not guaranteed throughput.

The app currently owns one process-local world. Additional Uvicorn workers would create separate worlds. A simulation owner with a command/snapshot boundary is future scaling work.

**---**

## 30. Events

Current events include births, successful theft, and each offered/accepted/rejected/expired/cancelled trade outcome. Events carry a unique ID, simulation tick/day, message, and relevant participant/item data.

Acceptance is logged after the successful exchange, so failed or repeated acceptance cannot emit a second accepted event. The frontend renders recent events beneath the map and in the header ticker.

The backend keeps only 100 events. Separate full-run counters or export are required for reliable experimental totals. Deaths, arrivals, injuries, groups, and predator events remain future logging or feature work.

**---**

## 31. Architecture

Current stack:

```text
Backend
Python
FastAPI
Simulation
Python agent/world systems
A* pathfinding
OpenSimplex procedural generation
PyTorch neural networks

Frontend
React
TypeScript
PixiJS

Infrastructure
Docker
Docker Compose
```

Docker Compose runs both the frontend and backend:

```bash
docker compose up --build
```

The simulation remains backend-driven.

The frontend **visualises simulation state** rather than deciding monkey behaviour.

### Current Simulation Structure

```text
World
├── terrain and trees
├── monkeys
│   ├── physical state
│   ├── traits
│   ├── memories
│   ├── action state
│   └── neural brain
├── tourists
├── reproduction
├── pathfinding
└── events
```

Long term, the neural system may move toward a shared `BrainManager`, batched inference and a more centralised replay/training architecture if individual per-monkey networks become too expensive.

---

## 32. Performance and Long-Run Simulation

Performance is now treated as a first-class engineering concern because the project needs to run hundreds of simulated days while supporting increasingly complex agents.

### Profiling

World-level profiling currently measures:

```text
world_update
monkeys
reproduction
cleanup
trees
tourists
```

Monkey-level profiling currently measures:

```text
total
observation
brain_state
brain_inference
action_execution
training
experience
survival_reward
tourist_logic
tourist_experience
movement
sleep
```

### Observation Reuse Optimisation

A major performance issue was repeated world observation during the same monkey update.

Previously, the same monkey could independently scan for nearby food, monkeys and tourists while:

```text
updating perception
building the brain state
checking valid actions
finalising the learning experience
```

The pre-action observation is now calculated once and reused by:

```text
brain-state construction
valid-action filtering
brain action selection
social interaction logic
tourist interaction logic
```

The next actual decision observation now supplies the preceding experience's `next_state` and valid-action mask. This includes intervening tourist offers and removes the former repeated post-action scan. Sleeping transitions accumulate reward until the next decision or death.

### Historical Benchmark Result

Before observation reuse:

```text
world_update: 948.397 ms/tick
monkeys:      940.599 ms/tick
```

After observation reuse:

```text
world_update: 703.706 ms/tick
monkeys:      696.653 ms/tick
```

This is approximately a **26% reduction in tick time**.

Historical monkey profile after the observation-reuse optimisation:

```text
total:              3.203 ms/monkey-update
observation:        1.308 ms/monkey-update
brain_state:        0.017 ms/monkey-update
brain_inference:    0.242 ms/monkey-update
action_execution:  0.413 ms/monkey-update
training:           0.027 ms/monkey-update
experience:         1.177 ms/monkey-update
survival_reward:    0.006 ms/monkey-update
tourist_logic:      0.000 ms/monkey-update
tourist_experience: 0.000 ms/monkey-update
movement:           0.002 ms/monkey-update
sleep:              0.000 ms/monkey-update
```

These timings were recorded before the current transition changes. They are historical evidence and need a matched-workload rerun before identifying current dominant costs.

### Performance Targets

Short-term target:

```text
< 500 ms/tick
```

Strong target before substantially increasing brain complexity:

```text
250–300 ms/tick
```

The purpose of optimisation is not just to make the UI feel faster. It is to make long-run experiments practical enough to observe reproduction, generational change, learned strategies and population dynamics.

### Likely Next Optimisations

- Profile food, monkey and tourist observation separately
- Reduce expensive tree scans using spatial/chunk-based lookup
- Reprofile observation and next-decision experience work after the implemented scan reuse
- Reuse A* paths when targets have not changed
- Avoid asking the neural brain for a completely new high-level decision every simulation tick
- Consider shared or batched neural inference later
- Add a fast/headless simulation mode for long experiments

## 33. Current Bugs / Technical Debt

### Population and Generational Stability

Long-run simulations previously showed a collapse in which the original adults aged into the elderly stage while too few offspring survived to adulthood.

One identified cause was juveniles remaining forced into the mother-follow pathway while their hunger increased, preventing them from independently seeking food. Juveniles should use the normal behaviour system while the hard mother-follow rule is reserved for infants.

Population debugging should track:

- Infants
- Juveniles
- Adults
- Elderly
- Adult males
- Adult females
- Reproduction-ready adults
- Births per day
- Deaths per day

### Performance

Reprofile the current update path after the next-decision transition change. Nearby-monkey visibility scans the population for every monkey, while shelter lookup scans loaded trees.

Existing observation timers already separate:

```text
fruit observation
monkey observation
tourist observation
```

Fruit visibility uses bounded tile/chunk lookup. Global nearest-fruit and nearest-shelter helpers still scan loaded trees. UI chunk requests also initialise tree chunks, so camera independence needs evaluation before browser-attached runs are considered reproducible.

### Brain Architecture

Each monkey currently owns its own brain and replay experience. This is simple and useful for experimentation but may become expensive as the population and action space grow.

Potential future work:

- Shared brain parameters
- Batched inference
- Central replay buffer
- Less frequent high-level decisions
- Separate simulation and training rates

Do not make these architectural changes until profiling shows they are necessary.

### Fruit and Resource Balance

Continue tuning fruit density and regeneration so scarcity exists without creating unavoidable population collapse.

### UI / Simulation Separation

The frontend should continue to render snapshots rather than becoming part of the simulation logic. Faster simulation modes should be able to reduce or disable frontend refresh frequency.

### Long-Run Testing

Long experiments should be used to validate:

- Population stability
- Reproduction
- Juvenile survival
- Resource pressure
- Brain behaviour
- Performance degradation over time

## 34. Development Order

### Phase 1 - Stabilisation and Performance

- Keep long-run population stable enough for multi-generation experiments
- Profile simulation bottlenecks
- Reduce observation cost
- Improve fast simulation speed
- Keep frontend rendering separate from simulation speed
- Continue validating reproduction and juvenile survival

### Phase 2 - Brain Foundations

- Keep the state vector interpretable
- Add brain-controlled actions incrementally
- Validate reward behaviour before adding more actions
- Track Q-values and training loss when debugging
- Avoid duplicate world scans inside decision logic

### Phase 3 - Tourist Observation

- Clickable tourists
- Tourist items
- Visible possessions
- Monkey tourist memory

### Phase 4 - Monkey-Tourist Interaction

Expand generic interactions:

- Investigate
- Watch
- Follow
- Scare
- Leave
- Grab item

### Phase 5 - Theft and Consequences (transfer implemented; difficulty remains)

Add:

- Steal difficulty
- Success/failure
- Tourist reactions
- Increased tourist awareness after robbery
- Item dropping / possession transfer rules

### Phase 6 - Tourist Economy (single-item exchange implemented; evaluation remains)

Add:

- Item return
- Food exchange
- Item value
- Risk/reward consequences

The brain should learn from these outcomes rather than being explicitly told that theft is profitable.

### Phase 7 - Parenting

Improve:

- Caretaker behaviour
- Infant feeding/support
- Orphan survival
- Child dependence
- Transition from infant dependency to juvenile independence

### Phase 8 - Social Relationships

Develop:

- Familiarity
- Relationships
- Rivalries
- Group formation

### Phase 9 - Competition

Expand:

- Food competition
- Territory
- Group competition
- Dominance

### Phase 10 - Environmental Danger

Introduce:

- Predators
- Threat detection
- Tree climbing
- Escape behaviour

### Phase 11 - Simulation Analysis (full-run population charts implemented)

Track:

- Population
- Generations
- Traits
- Survival
- Reproduction
- Learned action frequencies
- Tourist interactions
- Theft strategies
- Resource availability
- Performance over time

### Phase 12 - Scaling the Learning Architecture

Only when profiling shows it is worthwhile, investigate:

- Shared neural networks
- Batched inference
- Central replay buffers
- Separate training loops
- Headless experiment mode

## Design Principle

The central question of Project Simian is:

*>* ****Can interesting behaviour emerge from simple rules?****

Every new feature should therefore ask:

*>* ****Am I giving the monkey information and incentives, or am I directly telling it what interesting behaviour to perform?****

For example:

```python

if tourist.has_expensive_item():

    monkey.steal()

```

creates a monkey explicitly programmed to steal expensive objects.

Instead, give the monkey:

```text

limited perception

+

memory

+

hunger

+

visible tourist items

+

risky actions

+

consequences

+

reward history

```

Then observe whether valuable targets become preferable through experience.

That distinction should remain the central design principle as Project Simian grows.