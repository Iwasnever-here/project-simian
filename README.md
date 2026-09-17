# Simian Engine

Simian Engine is an agent-based simulation exploring how complex behaviour can emerge from simple rules.

The simulation places autonomous monkeys inside a procedurally generated island environment. Rather than scripting high-level outcomes directly, each monkey acts using local information such as its needs, traits, memory, surroundings, other monkeys, and tourists.

The long-term goal is to observe whether interesting strategies and social behaviours emerge from relatively simple underlying systems.

---

## Current Features

### Procedural World

- Procedurally generated island terrain
- OpenSimplex-based terrain generation
- Multiple terrain types
- 300 × 300 world
- Chunk-based rendering
- Interactive pan and zoom
- Minimap
- Day/night cycle

### Monkey Agents

Each monkey has individual traits including:

- Boldness
- Curiosity
- Sociability
- Memory
- Aggression

Monkeys also track internal state such as:

- Health
- Energy
- Hunger
- Age
- Life stage
- Sex
- Parents
- Known monkeys
- Known tourists

Agents can currently:

- Wander around the island
- Search for food
- Remember food locations
- Use A* pathfinding
- Eat fruit
- Lose energy through movement
- Take damage from starvation and exhaustion
- Sleep
- Reproduce
- Inherit traits from their parents
- Follow a parent while young
- Observe nearby monkeys
- Remember other monkeys
- Observe tourists
- Investigate tourists
- Watch, follow, or scare tourists depending on their traits

---

## Tourists

Tourists periodically arrive on the island by boat and travel toward the temple.

Their behaviour currently includes:

- Arriving near the temple in the morning
- Travelling to the temple
- Wandering around the temple area
- Entering the temple
- Staying for a random period
- Returning to the boat later in the day
- Leaving the island

Monkeys can observe tourists and remember information about them.

Tourists can also carry visible possessions. These possessions are intended to become part of a broader interaction system where monkeys may investigate, grab, exchange, drop, or learn from interactions with human objects.

The goal is to avoid explicitly scripting concepts such as "stealing". Instead, behaviours should emerge from more general actions and their consequences.

---

## Agent Memory

Monkeys have limited knowledge of the world.

They do not have access to the complete simulation state.

Instead, they build memories from things they have previously observed.

Examples include:

- Known food locations
- Known monkeys
- Last known monkey positions
- Known tourists
- Last known tourist positions
- Visible tourist possessions

This allows behaviour to depend on imperfect and potentially outdated information.

---

## Learning Direction

Simian Engine is gradually moving toward learned decision-making.

The simulation keeps two concepts separate:

1. Action selection
2. Action execution

For example, the simulation may provide an action such as:

```text
grab_item
```

The world determines whether that action is physically valid and executes it.

The monkey's decision system determines whether attempting that action is worthwhile.

Keeping these systems separate makes it possible to replace rule-based decision-making with learned policies later without rewriting the underlying simulation mechanics.

Current experiments also include recording agent experiences and training values for possible reinforcement-learning-based behaviour.

---

## Architecture

The project is split into a simulation backend and visual frontend.

### Backend

Built with:

- Python
- FastAPI

The backend is responsible for:

- Simulation state
- Monkey behaviour
- Tourist behaviour
- World generation
- Pathfinding
- Agent memory
- Reproduction
- Health and needs
- Interactions
- Simulation rules

### Frontend

Built with:

- React
- TypeScript
- Vite
- PixiJS

The frontend is responsible for:

- Rendering the world
- Rendering monkeys and tourists
- Camera controls
- Agent selection
- Entity inspectors
- Population information
- Event feeds
- Simulation controls
- Minimap rendering

The frontend does not control agent behaviour.

---

## Interface

The simulation UI currently contains:

- World viewport
- Top information bar
- Population panel
- Entity inspector
- Event feed
- Simulation time display
- Map position display
- Minimap
- Monkey and tourist selection

The main simulation viewport uses PixiJS and currently runs inside a fixed `900 × 600` render area.

---

## Running the Project

The easiest way to run Simian Engine is using Docker Compose.

### Requirements

Make sure the following are installed:

- Docker Desktop
- Docker Compose
- Git

Check Docker:

```bash
docker --version
```

Check Docker Compose:

```bash
docker compose version
```

---

### 1. Clone the Repository

```bash
git clone <repository-url>
```

Move into the project directory:

```bash
cd simian-engine
```

---

### 2. Start Docker Desktop

Make sure Docker Desktop is running before starting the project.

---

### 3. Build and Run

From the root of the project, run:

```bash
docker compose up --build
```

This builds and starts both the backend and frontend services.

The first build may take longer because Docker needs to install the project dependencies.

---

### 4. Open the Simulation

Once the containers are running, open:

```text
http://localhost:5173
```

in your browser.

This loads the React + PixiJS frontend.

---

## Backend

The simulation backend is built using FastAPI.

When the Docker containers are running, the backend runs as a separate service and provides the simulation state used by the frontend.

FastAPI's automatic API documentation can also be accessed through the backend's `/docs` endpoint if exposed by the Docker configuration.

For example:

```text
http://localhost:<backend-port>/docs
```

---

## Stopping the Simulation

To stop the running containers, press:

```text
Ctrl + C
```

inside the terminal running Docker Compose.

You can then remove the containers with:

```bash
docker compose down
```

---

## Rebuilding After Changes

If dependencies or Docker configuration have changed, rebuild using:

```bash
docker compose up --build
```

For normal code changes, the development environment may reload automatically depending on which service was changed.

---

## Viewing Running Containers

To see which containers are currently running:

```bash
docker ps
```

---

## Viewing Logs

To view Docker Compose logs:

```bash
docker compose logs
```

To continuously follow them:

```bash
docker compose logs -f
```

---

## Restarting the Project

If something gets stuck:

```bash
docker compose down
```

Then restart:

```bash
docker compose up --build
```

---

## Development Direction

Current priorities include:

- Improving tourist possession visibility
- Improving monkey memory of tourist possessions
- Generalising monkey/item interactions
- Adding difficulty and consequences to item grabbing
- Tourist reactions to monkey behaviour
- Item-for-food exchanges
- Remembering interaction outcomes
- Improving decision-making from previous experiences

Possible future systems include:

- More advanced social behaviour
- Monkey groups
- Tourist economies
- Emergent food-trading strategies
- Predators
- Disease
- More detailed statistics
- Learned behaviour using reinforcement learning or neural networks

These systems are intentionally being introduced gradually so that complex behaviour grows from understandable foundations rather than becoming a collection of scripted behaviours.

---

## Core Question

> How much complex behaviour can emerge from simple agents operating under limited information, memory, needs, personality traits, and environmental constraints?

That question drives the design of Simian Engine.
