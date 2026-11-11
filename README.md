# Simian Engine

Simian Engine is an agent-based simulation about how complex behaviour can emerge from simple rules. Autonomous monkeys live on a procedurally generated island, where they look for food, interact with each other, and encounter tourists. Their decisions depend on their needs, traits, and what they can see or remember.

The project explores whether monkeys can learn useful strategies for survival, social interaction, and trading.

## Current features

### Island and monkey behaviour

- A 300 × 300 island generated with OpenSimplex noise, with multiple terrain types, fruit trees, and a day/night cycle.
- Monkeys with individual traits, health, energy, hunger, age, and life stages.
- Food seeking, A* pathfinding, sleeping, reproduction, inherited traits, and young monkeys following a parent.
- Local perception and memory of food locations, nearby monkeys, tourists, and visible possessions.

### Tourists and trading

Tourists arrive by boat from 08:00, travel to the temple, and wander nearby or enter it. They begin returning to the boat at 17:00.

Monkeys can investigate, follow, scare, and steal from tourists. Stolen food can be eaten. Stolen valuables stay in the monkey’s inventory and can be returned in a trade.

A tourist who spots a nearby monkey holding one of their stolen valuables can offer food in exchange. The tourist offers the highest-value food they carry that costs no more than the stolen item. The monkey can accept, reject, or ignore the offer. Acceptance returns the exact stolen item and feeds the monkey. Offers expire after 30 ticks, and fleeing or departing can cancel them.

### Learning

Each monkey uses a PyTorch model to score the actions available to it. The simulation checks which actions are valid and handles their effects. Monkeys record experiences and train on rewards from outcomes such as finding food or losing health.

The learning curriculum introduces survival actions first, social actions from day 25, and more social actions from day 35. Tourist actions, including accepting and rejecting trades, unlock from **day 45**. Whether a trade happens depends on the tourist’s inventory, the agents’ positions, and the monkey’s decision.

### Interface

- Responsive PixiJS map with chunked rendering, pan and zoom, a minimap, and distinct monkey and tourist markers.
- Top controls for pausing, resuming, changing speed, and spawning monkeys.
- Population charts for alive monkeys, deaths, and total monkeys created. The charts show the full current run from day 0 using daily snapshots and the latest count.
- Monkey and tourist inspectors showing condition, behaviour, inventories, and pending trade offers. Portraits and items have square image placeholders.
- An event feed showing births, thefts, and offers that were made, accepted, rejected, expired, or cancelled.

Population history survives a browser refresh. Restarting the backend starts a new simulation because the world and its history are stored in memory.

## Architecture

| Part | Stack | Responsibility |
| --- | --- | --- |
| Backend | Python, FastAPI, PyTorch, OpenSimplex | World generation, simulation state, agent behaviour and learning, and API endpoints |
| Frontend | React, TypeScript, Vite, PixiJS | Map rendering, controls, entity inspectors, population charts, and the event feed |

## Run locally with Docker

Install Git and Docker Desktop with Docker Compose, then start Docker Desktop.

```bash
git clone https://github.com/Iwasnever-here/project-simian.git
cd project-simian
docker compose up --build
```

Open the [simulation](http://localhost:5173) in your browser. The backend runs on port `8000`, and its [interactive API documentation](http://127.0.0.1:8000/docs) lists the available endpoints.

| Endpoint | What it shows |
| --- | --- |
| [`/simulation/status`](http://127.0.0.1:8000/simulation/status) | Simulation speed, pause state, current population, and population history |
| [`/events`](http://127.0.0.1:8000/events) | The latest 100 simulation events. Search for `tourist_trade_accepted` to find completed trades. |
| `/monkeys/{id}/brain-debug` | A monkey’s training loss, experience count, and action scores |

Press `Ctrl+C` to stop an attached Compose session. Use `docker compose down` to stop and remove the containers.

```bash
docker compose ps
docker compose logs -f backend
```

The backend prints world and monkey performance profiles every 1,000 ticks. After changing backend Python code, run `docker compose restart backend` to load it. This resets the simulation. Rebuild with `docker compose up --build` after dependency or Docker configuration changes.

## Development checks

Run the backend tests from the repository root in the Python development environment.

```bash
python -m pytest backend/tests -q
```

Run the frontend checks from the `frontend` directory.

```bash
npm ci
npm run lint
npm run build
node --test tests/selection.test.mjs
```

## Development direction

The next step is to observe trading across longer simulation runs and see how often theft leads to an offer, which offers monkeys accept, and how those choices affect survival. Future work may explore more varied tourist responses, trade negotiation, and richer social behaviour among monkeys.

> How much complex behaviour can emerge from agents with limited information, memory, individual traits, and basic needs?