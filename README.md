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

Agents do not have global knowledge of the island. A monkey must first discover a resource before it can remember and navigate back to it.

### Genetic Traits

Each monkey has individual behavioural traits:

* Boldness
* Curiosity
* Sociability
* Memory
* Aggression

These traits provide the foundation for future inherited characteristics and trait-driven behaviour.

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

### Interactive Visualisation

* Interactive 2D island
* Camera movement
* Chunk-based terrain rendering
* Minimap
* Day/night visual effects
* Individual monkey selection
* Agent information display
* Live simulation state updates

---

# System Architecture

Project Simian separates the simulation engine from its visualisation.

The **Python backend** owns the world and simulation state. It generates terrain, manages resources and updates every monkey during simulation ticks.

The **React/PixiJS frontend** visualises the current simulation state and provides controls for interacting with the environment.

```text
┌──────────────────────────────┐
│      React + PixiJS UI       │
│                              │
│  World rendering             │
│  Monkey visualisation        │
│  Simulation controls         │
│  Agent inspection            │
└──────────────┬───────────────┘
               │
            HTTP API
               │
┌──────────────▼───────────────┐
│          FastAPI API         │
│                              │
│  World endpoints             │
│  Monkey endpoints            │
│  Simulation controls         │
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

Importantly, monkeys do not have access to the entire map. An agent must discover resources through its limited vision before that information can influence future decisions.

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

This separation allows future behaviours to reuse the same navigation system for food, shelter, social interaction, territories and other objectives.

---

# Memory System

Monkeys maintain their own spatial memory of useful locations.

A food memory can contain information such as:

```text
location
last_seen_tick
remembered_amount
```

This creates a distinction between the actual world state and what an individual monkey believes about the world.

For example, a monkey may remember that a tree contained fruit even though another monkey has since eaten it.

When hungry, an agent can recall a known food location and use the navigation system to calculate a path towards it.

The memory system provides the foundation for more advanced forgetting, learning and decision making.

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
POST /simulation/status
```

Chunk-based world endpoints allow the frontend to request only the terrain required for the current viewport rather than repeatedly transferring the entire world.

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

---

# Future Improvements

Project Simian is being developed incrementally, with each new system increasing the behavioural and evolutionary complexity of the simulation.

Planned features include:

* Genetic inheritance
* Reproduction
* Mutation
* Parent and offspring relationships
* Social groups
* Territorial behaviour
* Competition and aggression
* Trait-driven decision making
* Improved memory decay and reliability
* Learned behaviour
* Neural-network-based agent decision making
* Tourists and human-monkey interactions
* Larger and more complex simulated populations
* Simulation analytics and population statistics

A major future experiment will introduce tourists carrying food and valuable items.

Rather than explicitly programming monkeys to steal from tourists, the eventual aim is to investigate whether agents can learn strategies for obtaining food through interactions with tourists, including exchanging or stealing valuable objects, and whether successful behaviours spread through the population.

---

# Motivation

Project Simian was built to explore agent-based simulation, artificial intelligence and emergent behaviour through an environment where increasingly complex systems can be introduced incrementally.

Instead of directly scripting complex high-level behaviours, the project builds lower-level systems such as perception, spatial memory, navigation, survival pressure, genetics and resource competition that can interact to produce increasingly sophisticated agent behaviour.

The project demonstrates procedural generation, autonomous agent architecture, A* pathfinding, spatial memory, resource modelling, simulation design, API development, React/PixiJS visualisation and the performance challenges involved in running hundreds of independently simulated agents.
