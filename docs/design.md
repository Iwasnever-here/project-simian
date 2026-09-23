# Project Simian: Design Document

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

The mouse wheel should control map zoom while over the simulation rather than scrolling the webpage.

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

- Restore energy

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

The long-term central interaction is monkeys discovering that tourist belongings can produce food.

The monkey should ****not begin with knowledge that stealing an expensive item gets food****.

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

**---**

## 24. Current Learning System

The neural learning system is now active.

The current approach is a DQN-style reinforcement-learning system in which each monkey stores experiences containing:

```text
state
action
reward
next_state
done
```

The brain currently receives an 18-value state vector containing information such as:

```text
hunger
energy
health
boldness
curiosity
sociability
memory
aggression
maturity
day/night
food visibility
food distance
monkey visibility
monkey distance
tourist visibility
tourist distance
tourist item visibility
held-item state
```

### Monkey Actions

The wider monkey action vocabulary currently includes:

```text
wander
seek_food
seek_shelter
follow_mother
approach_monkey
avoid_monkey
follow_monkey
confront_monkey
socialise
investigate_tourist
watch_tourist
follow_tourist
scare_tourist
grab_item
leave_tourist
```

Only a subset is currently controlled by the main brain while the remaining systems are introduced incrementally.

The current brain-controlled set includes:

```text
wander
seek_food
seek_shelter
follow_mother
approach_monkey
```

Infants are still handled by the hard mother-follow rule before the normal brain decision pathway, so `follow_mother` should not be treated as a substitute for infant dependency logic.

### Reward

The reward signal is based on survival-related changes rather than directly rewarding a named behaviour.

Current reward components include:

```text
hunger improvement
health change
energy change
```

Food reward is scaled by how hungry the monkey was before eating, so reducing hunger is more valuable when the monkey genuinely needs food.

The project should continue avoiding rewards such as:

```text
+10 for stealing
```

Instead, actions should become useful because of the consequences they produce.

### Experience Replay and Training

Each monkey stores a bounded replay history and periodically samples batches for training.

Training uses predicted Q-values, discounted future Q-values and mean-squared error loss. Gradient clipping is used during optimisation.

Training is staggered across monkeys using their IDs and the world tick so that every monkey does not train on the same simulation tick.

### Current Learning Goal

The immediate goal is not to make the neural network control everything at once.

Instead:

```text
add one meaningful action
↓
verify state information
↓
verify reward signal
↓
observe behaviour
↓
profile performance
↓
then expand
```

This keeps the learned behaviour interpretable while the environment becomes more complex.

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

**---**

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

**---**

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

**---**

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

A fresh post-action observation is still generated for the reinforcement-learning `next_state`, because the learning transition must represent the world after the action.

### Benchmark Result

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

Current monkey profile after the optimisation:

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

The current dominant costs are therefore observation and post-action experience generation rather than neural-network training itself.

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
- Avoid repeated post-action work where the learning semantics can be preserved
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

The current largest CPU costs are monkey observation and creation of post-action learning experiences.

The next profiling step should split observation into:

```text
fruit observation
monkey observation
tourist observation
```

Tree lookup is a particularly important candidate because thousands of loaded trees may currently be scanned during visibility checks.

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

### Phase 5 - Theft and Consequences

Add:

- Steal difficulty
- Success/failure
- Tourist reactions
- Increased tourist awareness after robbery
- Item dropping / possession transfer rules

### Phase 6 - Tourist Economy

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

### Phase 11 - Simulation Analysis

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