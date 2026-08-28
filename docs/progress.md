# Project Simian: Progress

## Current Status

Project Simian currently has the foundations of the world simulation, autonomous monkey agents, reproduction and inheritance, social perception, memory, and the first tourist systems.

The current development focus is moving from the base monkey ecosystem toward meaningful **monkey-tourist interactions**.

---

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

---

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

---

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

---

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

---

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

---

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

---

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

---

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

---

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

---

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

---

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

---

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

- [ ] Use tourist memory to influence monkey behaviour
- [ ] Remember outcomes of tourist interactions
- [ ] Remember successful/failed theft attempts

---

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

---

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

---

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

---

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

---

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

---

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

---

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

---

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

---

## Tourist Items

### In Progress

- [x] Tourist item concept
- [x] Visible items represented in tourist memory
- [ ] Finish dedicated tourist item system
- [ ] Dedicated frontend item component
- [ ] Item steal difficulty
- [ ] Item value
- [ ] Different item types
- [ ] Tourist possession generation

Planned item properties:

```text
name
steal_score
value
```

---

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

---

## Theft

### Not Yet Implemented

Planned:

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

---

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

---

## Tree Safety

### Not Yet Implemented

Planned:

- [ ] Monkeys can identify safe trees
- [ ] Monkeys flee toward trees
- [ ] Tree climbing
- [ ] Ground predators cannot reach monkey
- [ ] Monkey waits until threat disappears
- [ ] Traits influence flee decisions

---

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

---

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

---

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

---

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

---

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

---

# Current Development Focus

The immediate focus is:

```text
Tourists
↓
Visible items
↓
Monkey observes tourist
↓
Monkey remembers tourist + possessions
↓
Basic monkey-tourist interaction
↓
Stealing
↓
Tourist reaction
↓
Item-for-food exchange
↓
Monkey remembers outcome
```

The next major milestone is therefore:

> **A monkey can observe a tourist carrying an item, attempt to steal it, experience the tourist's response, and receive a meaningful consequence.**

Learning should **not** be introduced before this loop works reliably.

---

# Next Steps

1. [ ] Fix current popup error
2. [ ] Finish tourist item representation
3. [ ] Finish tourist clicking / inspection
4. [ ] Verify monkey tourist memory
5. [ ] Add basic monkey approach/ignore tourist decisions
6. [ ] Implement stealing attempts
7. [ ] Implement steal difficulty
8. [ ] Implement tourist reaction
9. [ ] Increase tourist caution after robbery
10. [ ] Implement item return for food
11. [ ] Store interaction outcomes in monkey memory
12. [ ] Test whether different monkey traits produce different strategies

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