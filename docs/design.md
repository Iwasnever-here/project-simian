# Project Simian: Design Document

## Core Idea

**Project Simian** is an agent-based simulation exploring whether complex social and economic behaviour can emerge from relatively simple individual rules.

The simulation takes place on a procedurally generated island inhabited by autonomous monkeys. Monkeys have limited perception, memory, physical needs, behavioural traits and inherited characteristics.

The long-term goal is to introduce tourists and a temple economy, allowing monkeys to discover behaviours such as stealing valuable objects, exchanging stolen items for food, competing over profitable locations and potentially developing group strategies without those behaviours being directly scripted.

---

## 1. World Generation

### Terrain

The island is procedurally generated using **OpenSimplex noise**.

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

---

## 2. World Rendering

### Chunk Loading

Divide the world into:

```text
32 × 32 tile chunks
```

Only render chunks visible within or close to the player's viewport.

The **simulation itself continues across the whole world**. Chunking is a rendering optimisation, not a simulation boundary.

### Camera

The player can:

- Pan around the world
- Zoom in and out
- Click monkeys
- Click tourists
- Inspect entities without affecting the simulation

The mouse wheel should control map zoom while over the simulation rather than scrolling the webpage.

### Minimap

Display a small minimap showing:

- Entire island
- Simplified terrain
- Current camera position
- Camera viewport rectangle

Potential later feature:

- Click minimap to move camera

---

## 3. Environment and Resources

### Trees

Trees spawn according to suitable terrain/environment conditions.

Some trees produce fruit.

Different areas of the island therefore naturally contain different amounts of food.

### Fruit

Fruit acts as one of the monkeys' primary food sources.

Fruit should:

- Restore energy
- Respawn over time
- Exist at specific locations
- Become depleted when eaten

Respawn rates should be slow enough that monkeys actually need to search and compete rather than camping beside an infinite food source.

---

## 4. Monkey Agents

Every monkey is an independent agent.

A monkey does **not** have global knowledge of the simulation.

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

---

## 5. Life Stages

Monkeys progress through:

```text
Infant
Juvenile
Adult
Elderly
```

Age affects capability and vulnerability.

### Infants

- Highly vulnerable
- Dependent on a caretaker
- Poor survival ability alone
- Cannot reproduce

### Juveniles

- More independent
- Still less capable than adults
- May continue following their mother
- Cannot reproduce

### Adults

- Highest general survival ability
- Can reproduce
- Can raise offspring

### Elderly

- Increased physical vulnerability
- Potentially retain advantages from experience and memory

Older monkeys can therefore become physically weaker while potentially being behaviourally more experienced.

---

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

---

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

---

## 8. Day and Night

The simulation contains a continuous day/night cycle.

Time influences behaviour.

### Sleeping

Monkeys need sleep.

Sleeping during the night should generally be safer than sleeping during the day.

However, staying still should not automatically mean being safe.

A sleeping or stationary monkey may still be vulnerable to predators or other threats.

This makes **where and when a monkey rests** meaningful.

---

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

---

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

The monkey can use **A\*** to navigate toward remembered resources.

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

---

## 11. Pathfinding

Monkeys and tourists use **A\*** pathfinding.

Pathfinding should account for:

- Impassable terrain
- Terrain boundaries
- Destination
- Failed routes

Failed pathfinding should not trigger another expensive A\* search every simulation tick.

A retry cooldown can be used before attempting the route again.

---

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

---

## 13. Reproduction

Adult monkeys can reproduce when conditions allow.

Requirements include:

- Compatible adult partner
- Minimum health
- Minimum energy
- Reproduction cooldown completed

Reproduction pairing should be controlled by the **World/simulation layer** rather than letting both monkeys independently spawn offspring.

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

---

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

---

## 15. Parenting

Young monkeys should depend on adults.

Initially, infants can remain near their mother/caretaker.

The system can later expand into:

- Following mother
- Protection
- Food assistance
- Learning through observation
- Separation as they mature

### Orphan Survival

If a monkey is younger than approximately 50 days and its mother dies, its probability of survival should fall significantly.

Do not simply kill the infant.

Instead remove the advantages provided by parenting.

This creates an emergent survival consequence rather than:

```text
mother_dead = infant_dead
```

---

## 16. Social Behaviour

Monkeys perceive nearby monkeys and react differently depending on their traits and circumstances.

Possible interactions:

- Approach
- Avoid
- Follow
- Compete
- Ignore

Sociability, aggression, hunger, age and relationships should all contribute to these decisions.

---

## 17. Groups

A major future system is spontaneous group formation.

Groups should ideally **emerge from repeated interactions**, rather than monkeys being randomly assigned to teams.

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

---

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

---

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

---

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

---

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

---

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

---

## 23. Robbery / Theft

The long-term central interaction is monkeys discovering that tourist belongings can produce food.

The monkey should **not begin with knowledge that stealing an expensive item gets food**.

Instead:

```text
Monkey encounters tourist
↓
Notices visible item
↓
Attempts interaction / theft
↓
Tourist reacts
↓
Monkey experiences outcome
↓
Information influences future behaviour
```

This is where the project can eventually move from rule-based agents toward actual learning.

### Tourist Response

After being robbed once:

```text
awareness / steal difficulty increases
```

for their remaining possessions until they leave the island.

Repeatedly targeting one tourist therefore becomes progressively harder.

This creates a natural incentive to choose targets.

---

## 24. Future Learning System

Do **not** introduce the neural network yet.

The simulation first needs a stable environment in which learning has something meaningful to optimise.

Before learning, the world needs:

```text
tourists
+
items
+
stealing
+
rewards
+
punishments
+
memory
+
competition
```

Only then does a learned monkey brain become useful.

Potential observations might eventually include:

```text
hunger
energy
nearby tourists
visible items
tourist behaviour
nearby monkeys
distance to safety
memory of previous outcomes
```

Possible actions:

```text
ignore
approach
follow
steal
retreat
hide
```

Rewards should arise naturally from survival and resource acquisition rather than directly rewarding `stealing`.

---

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

---

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

---

## 27. Simulation Statistics

The UI should track important population-level information.

Examples:

- Current living population
- Total births
- Total deaths
- Population over time
- Age distribution
- Average behavioural traits
- Food availability
- Tourist count
- Successful thefts
- Failed thefts
- Items stolen
- Causes of death

Later, tracking traits across generations becomes particularly valuable.

For example:

```text
Average boldness

Generation 1: 0.49
Generation 5: 0.53
Generation 15: 0.67
```

This makes it possible to investigate whether the environment is selecting for certain behaviours rather than relying on visual impressions.

---

## 28. Entity Inspection UI

Clicking a monkey should expose information such as:

```text
Name
Age
Life stage
Sex
Health
Energy
Traits
Parents
Current behaviour
Known monkeys
Known tourists
```

Tourists should also be clickable.

Tourist information could include:

```text
State
Current destination
Time on island
Visible possessions
Behavioural traits
Whether previously robbed
```

Items should have their own UI component rather than placing all item display logic directly inside the tourist component.

---

## 29. Simulation Controls

The UI should support:

- Pause
- Resume
- Simulation speed
- Time/day display
- Camera zoom
- Camera pan

Backend simulation state separates:

```text
simulation_paused
simulation_speed
```

from the underlying world.

---

## 30. Events

Important events can be surfaced beneath or alongside the world.

Examples:

```text
Monkey born
Monkey died
Tourist boat arrived
Monkey stole item
Monkey injured
Group formed
Predator attack
```

Events should remain selective.

Generating an event for every piece of fruit eaten would make the event feed noisy and less useful.

---

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

The simulation should remain primarily backend-driven.

The frontend **visualises simulation state** rather than deciding monkey behaviour.

---

## 32. Current Bugs / Technical Debt

### Population Tracking

Population statistics must update correctly when monkeys:

- Spawn
- Are born
- Die

Avoid deriving the living population from an outdated initial-population counter.

### Popup Error

Fix the current entity popup error before layering more UI systems onto it.

### Minimap

Resolve the current minimap rendering issue.

### Life Stage Display

Ensure stage information is correctly passed from backend to frontend.

### Alive / Dead State

Frontend representation must correctly reflect backend death state.

### Simulation Controls

Pause and speed controls need to correctly modify backend simulation state.

### Fruit Respawning

Tune fruit regeneration so scarcity actually exists.

### Canvas Scrolling

Capture mouse-wheel input over the PixiJS canvas so zooming doesn't scroll the page.

---

## 33. Development Order

### Phase 1 - Stabilisation

- Fix popup error
- Fix population tracking
- Fix stage/alive display
- Fix minimap
- Fix simulation controls
- Balance fruit respawning

### Phase 2 - Tourist Observation

- Clickable tourists
- Tourist items
- Visible possessions
- Monkey tourist memory

### Phase 3 - Monkey-Tourist Interaction

Implement basic interactions without learning.

### Phase 4 - Theft

Add:

- Steal difficulty
- Success/failure
- Tourist reactions
- Increased tourist awareness after robbery

### Phase 5 - Tourist Economy

Add:

- Item return
- Food exchange
- Item value
- Risk/reward decisions

### Phase 6 - Experience Memory

Allow monkeys to associate previous interactions with outcomes.

### Phase 7 - Parenting

Improve:

- Caretaker behaviour
- Orphan survival
- Child dependence

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

### Phase 11 - Simulation Analysis

Track:

- Population
- Generations
- Traits
- Survival
- Reproduction
- Theft strategies
- Tourist interactions

### Phase 12 - Learned Behaviour

Only once the environment and reward systems are stable should neural networks or another learning system be introduced.

---

## Design Principle

The central question of Project Simian is:

> **Can interesting behaviour emerge from simple rules?**

Every new feature should therefore ask:

> **Am I giving the monkey information and incentives, or am I directly telling it what interesting behaviour to perform?**

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