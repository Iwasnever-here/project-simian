# Project Simian

Project Simian is an agent-based ecosystem simulation where autonomous monkeys survive within a procedurally generated island environment.

Rather than giving agents access to the entire simulation state, each monkey operates using limited vision, internal needs and its own memory of the environment. Monkeys explore the island, discover resources, remember useful locations and use A* pathfinding to navigate towards known resources.

The long-term goal is to progressively introduce genetics, social behaviour, learning and human interaction to explore how increasingly complex behaviour can emerge from relatively simple agent rules.

---

## Features

### Procedural World Generation

* Procedurally generated island terrain
* Multiple terrain types
* Forests and fruit-bearing trees
* Resource distribution across the environment
* Chunk-based world loading
* Day and night cycle

### Autonomous Monkey Agents

* Independent monkey agents
* Wandering and exploration
* Food-seeking behaviour
* Sleeping and energy management
* Hunger management
* Health system
* Age and life stages
* Agent mortality
* Limited vision range
* Individual behavioural traits
* Reproduction between compatible adult monkeys
* Parent and offspring relationships
* Genetic trait inheritance and mutation
* Caretaker following behaviour for young monkeys

### Navigation & Pathfinding

* A* pathfinding for agent navigation
* Navigation towards remembered resources
* Obstacle-aware movement
* Path generation between agents and target locations
* Centralised agent movement logic

Monkeys can remember the coordinates of discovered resources and later calculate a valid path back to them rather than moving blindly towards their target.

### Agent Memory

* Monkeys remember discovered food locations
* Stored resource coordinates
* Limited number of food memories
* Remembered resource quantities
* Memory timestamps for discovered resources
* Memories used by the navigation system
* Memories of other monkeys
* Memories of tourists
* Last known positions of observed agents
* Memories of visible tourist items

Agents do not have global knowledge of the island. A monkey must first discover a resource or observe another agent before that information can influence future decisions.

### Genetic Traits

Each monkey has individual behavioural traits:

* Boldness
* Curiosity
* Sociability
* Memory
* Aggression

These traits can be inherited from parents with mutation, allowing behavioural characteristics to vary across generations and providing the foundation for trait-driven behaviour.

### Reproduction & Inheritance

* Reproduction between compatible adult monkeys
* Reproduction health and energy requirements
* Reproduction cooldowns
* Parent tracking
* Genetic trait inheritance
* Trait mutation between generations
* Infant and juvenile caretaker relationships
* Young monkeys follow their caretaker

### Tourist Simulation

* Scheduled tourist arrivals and departures
* Tourists travel from the boat landing to the temple
* Temple wandering behaviour
* Temple entry behaviour
* Tourist state tracking
* Tourist inventories containing valuable items
* Monkeys can perceive nearby tourists through limited vision
* Monkeys can remember previously seen tourists
* Monkeys can remember visible tourist possessions
* Early tourist investigation behaviour for curious monkeys
* Tourist and monkey selection through the frontend inspector

### Resource Simulation

* Fruit-bearing trees
* Limited fruit supply
* Fruit harvesting
* Resource depletion
* Fruit regeneration over time
* Competition for finite environmental resources

### Simulation Controls

* Pause and resume simulation
* Adjustable simulation speed
* Spawn multiple monkeys
* Track simulation day and time
* Support for hundreds of simulated agents
* Backend-owned population statistics
* Live alive, death and total population tracking

### Interactive Visualisation

* Interactive 2D island
* Camera movement and panning
* Zoom controls
* Chunk-based terrain rendering
* Minimap
* Day/night visual effects
* Individual monkey and tourist selection
* Agent and tourist information display
* Live simulation state updates
* Event ticker
* Simulation event feed
* Fixed 900 × 600 simulation viewport for stable PixiJS rendering

---

# System Architecture

Project Simian separates the simulation engine from its visualisation.

The **Python backend** owns the world and simulation state. It generates terrain, manages resources and updates every monkey and tourist during simulation ticks.

The **React/PixiJS frontend** visualises the current simulation state and provides controls for interacting with the environment.

```text
┌──────────────────────────────┐
│      React + PixiJS UI       │
│                              │
│  World rendering             │
│  Monkey / tourist rendering  │
│  Simulation controls         │
│  Agent inspection            │
│  Event visualisation         │
└──────────────┬───────────────┘
               │
            HTTP API
               │
┌──────────────▼───────────────┐
│          FastAPI API         │
│                              │
│  World endpoints             │
│  Monkey endpoints            │
│  Tourist endpoints           │
│  Simulation controls         │
│  Event endpoints             │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│       Simulation Engine      │
│                              │
│  Procedural world            │
│  Agent behaviour             │
│  Memory                      │
│  A* pathfinding              │
│  Resources                   │
│  Health / survival           │
│  Reproduction / genetics     │
│  Tourist simulation          │
│  Day-night simulation        │
└──────────────────────────────┘
```

Keeping the simulation independent from the rendering layer allows the backend to continue updating the world regardless of frontend rendering performance.

---

# Agent Behaviour

Each monkey maintains its own internal state, including:

* Position
* Hunger
* Energy
* Health
* Age
* Life stage
* Current behaviour
* Movement target
* Environmental memories
* Genetic traits
* Parent relationships
* Caretaker relationships
* Reproduction state
* Memories of other monkeys
* Memories of tourists and visible tourist items

Monkeys currently use rule-based decision making to determine what they should do during each simulation tick.

A simplified food-seeking cycle looks like:

```text
Wandering
    ↓
Discover food
    ↓
Remember location
    ↓
Become hungry
    ↓
Recall visible / remembered food
    ↓
Calculate A* path
    ↓
Navigate to resource
    ↓
Eat
    ↓
Continue exploring
```

Energy, hunger, health and environmental conditions place survival pressure on the agents.

Adult monkeys can reproduce when compatibility, health, energy and reproduction cooldown requirements are satisfied. Offspring inherit behavioural traits from their parents with mutation, allowing traits to change across generations. Young monkeys can also maintain caretaker relationships and follow their caretaker during early life stages.

Monkeys can also perceive nearby tourists. Observed tourists can be stored in memory along with their last known position and visible possessions. Curious monkeys can investigate tourists, providing the first stage of human-monkey interaction within the simulation.

Importantly, monkeys do not have access to the entire map. An agent must discover resources and observe other agents through its limited vision before that information can influence future decisions.

---

# Reproduction & Genetics

Adult monkeys can reproduce when simulation requirements such as life stage, health, energy and reproduction cooldowns are satisfied.

Offspring maintain parent relationships and inherit behavioural traits from both parents. Small mutations are applied during inheritance, allowing traits to gradually diverge across generations.

```text
Parent A traits
      +
Parent B traits
      ↓
Trait inheritance
      ↓
Mutation
      ↓
Child traits
```

Young monkeys can maintain a caretaker relationship and follow their caretaker, introducing the first parent-offspring social behaviour into the simulation.

Reproduction is coordinated by the simulation layer rather than allowing individual agents to directly create offspring, preventing duplicate births during the same simulation tick.

---

# Navigation System

When an agent selects a destination, A* search is used to find a valid route through the environment.

This allows navigation to operate independently from high-level decision making. The behaviour system decides **where** a monkey wants to go, while the navigation system determines **how** it gets there.

```text
Agent Decision
      ↓
Select Target
      ↓
A* Search
      ↓
Generate Path
      ↓
Follow Path
      ↓
Reach Target
```

This separation allows future behaviours to reuse the same navigation system for food, social interaction, tourists, territories and other objectives.

---

# Memory System

Monkeys maintain their own memories of resources and agents they have encountered.

A food memory can contain information such as:

```text
location
last_seen_tick
remembered_amount
```

This creates a distinction between the actual world state and what an individual monkey believes about the world.

For example, a monkey may remember that a tree contained fruit even though another monkey has since eaten it.

When hungry, an agent can recall a known food location and use the navigation system to calculate a path towards it.

Monkeys can also remember other monkeys. These memories can contain the other monkey's identity, last observed position and the simulation tick when it was last seen.

Tourist memories can similarly store:

```text
tourist_id
last_x
last_y
last_seen_tick
visible_items
```

This allows social and tourist-facing decisions to depend on information an individual monkey has actually observed rather than global simulation state.

The memory system provides the foundation for more advanced forgetting, learning and decision making.

---

# Tourist System

Tourists introduce human agents into the ecosystem.

Tourists arrive at a boat landing and travel towards the temple. Once there, they can wander around the temple area and may enter the temple for a period of time. At the end of their visit, tourists return towards the boat.

Tourists can carry items with different values. These possessions provide the foundation for future interactions between monkeys and tourists.

```text
Boat arrival
      ↓
Travel to temple
      ↓
Wander around temple
      ↓
Potentially enter temple
      ↓
Return to boat
      ↓
Leave island
```

Monkeys do not automatically know where tourists are or what they possess. A tourist must enter a monkey's limited vision before the monkey can observe and remember them.

Curiosity can influence whether a monkey investigates an observed tourist.

This system provides the foundation for future stealing, trading, food exchange and learned human-monkey interaction.

---

# Resource System

Food within the environment is finite.

Fruit trees contain a limited quantity of fruit that monkeys can consume. Once depleted, fruit regenerates gradually over future simulation ticks.

```text
Tree
├── position
├── species
├── fruit
├── maximum fruit
├── regeneration state
└── alive
```

This prevents agents from surviving indefinitely from unlimited resources and introduces competition between monkeys occupying the same environment.

---

# Application Structure

The project is divided into separate backend simulation and frontend visualisation systems.

```text
project--simian/

├── backend/
│   ├── api/
│   └── simulation/
│       ├── agents/
│       └── world/
│
└── frontend/
    └── src/
        ├── components/
        ├── services/
        └── ...
```

The backend contains the simulation rules and authoritative world state, while the frontend consumes the API and renders the resulting environment.

---

# Technology Stack

## Simulation / Backend

* Python
* FastAPI
* OpenSimplex
* Uvicorn

## Frontend

* React
* TypeScript
* PixiJS
* Vite

## Infrastructure

* Docker
* Docker Compose

---

# API

The FastAPI backend exposes simulation state to the frontend.

Current endpoints include:

```text
GET  /world/meta

GET  /world/chunk/{cx}/{cy}

GET  /world

GET  /monkeys

GET  /monkeys/{id}

POST /monkeys/spawn

GET  /tourists

GET  /tourists/{id}

GET  /temple

GET  /boat-landing

GET  /events

GET  /simulation/status

POST /simulation/pause

POST /simulation/resume

POST /simulation/speed/{speed}
```

Chunk-based world endpoints allow the frontend to request only the terrain required for the current viewport rather than repeatedly transferring the entire world.

The backend is also the authoritative source for population statistics. Monkey creation, including initial spawning, manual spawning and reproduction, is tracked by the simulation engine. The frontend consumes alive, death and total population values from the simulation status endpoint rather than reconstructing population history itself.

---

# Running Locally

## Clone the repository

```bash
git clone https://github.com/your-username/project--simian.git

cd project--simian
```

## Start the Backend

Create and activate a Python virtual environment, then install the dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI development server:

```bash
uvicorn backend.api.main:app --reload
```

## Start the Frontend

```bash
cd frontend

npm install

npm run dev
```

The frontend can then communicate with the locally running simulation API.

## Run with Docker

The full application can be built and started with Docker Compose:

```bash
docker compose up --build
```

Docker Compose builds and runs both the FastAPI simulation backend and the React frontend, providing a reproducible environment for the complete application.

---

# Future Improvements

Project Simian is being developed incrementally, with each new system increasing the behavioural and evolutionary complexity of the simulation.

Planned features include:

* More advanced social groups
* Territorial behaviour
* Stronger trait-driven aggression and competition
* Improved memory decay and reliability
* More advanced tourist investigation
* Item stealing behaviour
* Trading and food exchange with tourists
* Learned behaviour
* Social learning between monkeys
* Neural-network-based agent decision making
* Larger and more complex simulated populations
* Expanded simulation analytics and generational statistics

Tourists carrying valuable items are now present in the simulation and follow a daily route between the boat landing and temple. Monkeys can perceive nearby tourists, remember them and inspect information about visible possessions.

The next major experiment is to move from observation and investigation towards economic interaction.

Rather than permanently scripting one fixed stealing strategy, the long-term aim is to investigate whether agents can learn useful strategies for obtaining food through tourists, including exchanging or stealing valuable objects, and whether successful behaviours spread through the population.

---

# Motivation

Project Simian was built to explore agent-based simulation, artificial intelligence and emergent behaviour through an environment where increasingly complex systems can be introduced incrementally.

Instead of directly scripting complex high-level behaviours, the project builds lower-level systems such as perception, spatial memory, navigation, survival pressure, genetics, social interaction and resource competition that can interact to produce increasingly sophisticated agent behaviour.

The project demonstrates procedural generation, autonomous agent architecture, A* pathfinding, spatial and social memory, genetics, tourist simulation, resource modelling, simulation design, API development, Docker Compose containerisation, React/PixiJS visualisation and the performance challenges involved in running hundreds of independently simulated agents.
