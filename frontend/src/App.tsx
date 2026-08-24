import { useEffect, useState } from 'react'
import WorldCanvas from './WorldCanvas'
import Minimap from './Minimap'

type WorldMeta = {
  width: number
  height: number
  chunkSize: number
  day: number
  hour: number
  isDaytime: boolean
}

type Viewport = {
  x: number
  y: number
  width: number
  height: number
}

type SimulationStatus = {
  paused: boolean
  speed: number
  alive: number
  total: number
  deaths: number
}

type Monkey = {
  id: number
  x: number
  y: number
  hunger: number
  age: number
  life_stage: string
  health: number
  alive: boolean
  name: string
  gender: string
  energy: number
  state: string
  target_monkey_id: number | null
  traits: {
    boldness: number
    curiosity: number
    sociability: number
    memory: number
    aggression: number
    effective_memory: number
  }
}

type SimulationEvent = {
  id: number
  type: string
  message: string
  tick: number
  day: number
  data: {
    child_id?: number
    child_name?: string
    parent_ids?: number[]
    parent_names?: string[]
  }
}

type Tourist = {
  id: number
  name: string
  value: number
  x: number
  y: number
  alive: boolean
  items: {
    name: string
    value: number
  }[]
}
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

function App() {
  const [worldMeta, setWorldMeta] = useState<WorldMeta | null>(null)
  const [viewport, setViewport] = useState<Viewport | null>(null)

  const [aliveMonkeys, setAliveMonkeys] = useState<number | null>(null)
  const [totalMonkeys, setTotalMonkeys] = useState<number | null>(null)
  const [monkeyDeaths, setMonkeyDeaths] = useState<number | null>(null)
  const [spawning, setSpawning] = useState(false)

  const [paused, setPaused] = useState<boolean | null>(null)
  const [simulationSpeed, setSimulationSpeed] = useState<number | null>(null)

  const [selectedMonkeyId, setSelectedMonkeyId] = useState<number | null>(null)
  const [selectedMonkey, setSelectedMonkey] = useState<Monkey | null>(null)

  const [selectedTouristId, setSelectedTouristId] = useState<number | null>(null)
  const [selectedTourist, setSelectedTourist] = useState<Tourist | null>(null)

  const [events, setEvents] = useState<SimulationEvent[]>([])

  const formatTime = (hour: number) => {
    const wholeHour = Math.floor(hour)
    const minutes = Math.floor((hour - wholeHour) * 60)

    return `${String(wholeHour).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
  }

  // -----------------------------------------------------------------
  // World meta
  // -----------------------------------------------------------------

  useEffect(() => {
    const fetchWorldMeta = () => {
      fetch(`${API_BASE}/world/meta`)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`)
          }

          return response.json()
        })
        .then((data: WorldMeta) => {
          setWorldMeta(data)
        })
        .catch((error) => {
          console.error('World meta fetch failed:', error)
        })
    }

    fetchWorldMeta()

    const interval = window.setInterval(fetchWorldMeta, 1000)

    return () => {
      window.clearInterval(interval)
    }
  }, [])

  // -----------------------------------------------------------------
  // Simulation status
  // -----------------------------------------------------------------

  useEffect(() => {
    const fetchStatus = () => {
      fetch(`${API_BASE}/simulation/status`)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`)
          }
          return response.json()
        })
        .then((data: SimulationStatus) => {
          setPaused(data.paused)
          setSimulationSpeed(data.speed)

          setAliveMonkeys(data.alive)
          setTotalMonkeys(data.total)
          setMonkeyDeaths(data.deaths)
        })
        .catch((error) => {
          console.error('Simulation status fetch failed:', error)
        })
    }

    fetchStatus()

    const interval = window.setInterval(fetchStatus, 1000)

    return () => {
      window.clearInterval(interval)
    }
  }, [])

  // -----------------------------------------------------------------
  // Selected monkey
  // -----------------------------------------------------------------

  useEffect(() => {
    if (selectedMonkeyId === null) {
      setSelectedMonkey(null)
      return
    }

    const fetchSelectedMonkey = () => {
      fetch(`${API_BASE}/monkeys/${selectedMonkeyId}`)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`)
          }

          return response.json()
        })
        .then((data: Monkey) => {
          setSelectedMonkey(data)
        })
        .catch((error) => {
          console.error('Selected monkey fetch failed:', error)
        })
    }

    fetchSelectedMonkey()

    const interval = window.setInterval(fetchSelectedMonkey, 1000)

    return () => {
      window.clearInterval(interval)
    }
  }, [selectedMonkeyId])
  // -----------------------------------------------------------------
  // Selected tourist
  // -----------------------------------------------------------------

  useEffect(() => {
    if (selectedTouristId === null) {
      setSelectedTourist(null)
      return
    }

    const fetchSelectedTourist = () => {
      fetch(`${API_BASE}/tourists/${selectedTouristId}`)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`)
          }

          return response.json()
        })
        .then((data: Tourist) => {
          setSelectedTourist(data)
        })
        .catch((error) => {
          console.error('Selected tourist fetch failed:', error)
        })
    }

    fetchSelectedTourist()

    const interval = window.setInterval(
      fetchSelectedTourist,
      1000,
    )

    return () => {
      window.clearInterval(interval)
    }
  }, [selectedTouristId])

  // -----------------------------------------------------------------
  // Simulation events
  // -----------------------------------------------------------------

  useEffect(() => {
    const fetchEvents = () => {
      fetch(`${API_BASE}/events`)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`)
          }

          return response.json()
        })
        .then((data: SimulationEvent[]) => {
          setEvents(data)
        })
        .catch((error) => {
          console.error('Events fetch failed:', error)
        })
    }

    fetchEvents()

    const interval = window.setInterval(fetchEvents, 1000)

    return () => {
      window.clearInterval(interval)
    }
  }, [])

  // -----------------------------------------------------------------
  // Controls
  // -----------------------------------------------------------------

  const handleSpawnMonkey = () => {
    setSpawning(true)

    fetch(`${API_BASE}/monkeys/spawn`, { method: 'POST' })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        return response.json()
      })
      .catch((error) => {
        console.error('Spawn monkey failed:', error)
      })
      .finally(() => {
        setSpawning(false)
      })
  }

  const handlePauseToggle = async () => {
    if (paused === null) {
      return
    }

    const endpoint = paused ? '/simulation/resume' : '/simulation/pause'

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, { method: 'POST' })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: SimulationStatus = await response.json()

      setPaused(data.paused)
      setSimulationSpeed(data.speed)
    } catch (error) {
      console.error('Simulation pause/resume failed:', error)
    }
  }

  const handleSpeedChange = async (speed: number) => {
    try {
      const response = await fetch(`${API_BASE}/simulation/speed/${speed}`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: SimulationStatus = await response.json()

      setPaused(data.paused)
      setSimulationSpeed(data.speed)
    } catch (error) {
      console.error('Simulation speed change failed:', error)
    }
  }

  return (
    <div
      className="bg-(--background)"
      style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center' }}
    >
      {/* Top bar */}
      <div className="w-screen grid grid-cols-[1fr_auto_1fr] items-center p-4 px-10">
        {/* Left - world time */}
        <div className="flex justify-start text-2xl">
          {worldMeta && (
            <span style={{ fontSize: 18 }}>
              Day {worldMeta.day}
              {' · '}
              {formatTime(worldMeta.hour)}{' '}
              {worldMeta.isDaytime ? '☀️' : '🌙'}
            </span>
          )}
        </div>

        {/* Centre - title */}
        <h1 style={{ margin: 0, fontSize: 42 }}>Project Simian</h1>

        {/* Right - controls */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 8 }}>
          <button
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            onClick={handlePauseToggle}
            disabled={paused === null}
          >
            {paused === null ? 'Loading...' : paused ? '▶ Resume' : '⏸ Pause'}
          </button>

          {[0.5, 1, 2, 4].map((speed) => (
            <button
              className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
              key={speed}
              onClick={() => handleSpeedChange(speed)}
              disabled={simulationSpeed === null || simulationSpeed === speed}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>

      {/* Main simulation area */}
      {worldMeta && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '370px 900px 370px',
            gap: 35,
            alignItems: 'start',
          }}
        >
          {/* Population */}
          <div className="h-[600px] border border-white p-4 rounded-lg">
            <h3 className="text-xl font-semibold mb-4">Population</h3>

            <button
              className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
              onClick={handleSpawnMonkey}
              disabled={spawning}
            >
              {spawning ? 'Spawning...' : 'Spawn Monkey'}
            </button>

            <div className="flex flex-col gap-2">
              <div>Alive: {aliveMonkeys ?? '...'}</div>
              <div>Deaths: {monkeyDeaths ?? '...'}</div>
              <div>Total: {totalMonkeys ?? '...'}</div>
            </div>
          </div>

          {/* World + Events */}
          <div style={{ width: 900 }}>
            {/* World */}
            <div style={{ position: 'relative', width: 900, height: 700 }}>
              <WorldCanvas
                worldMeta={worldMeta}
                apiBase={API_BASE}
                onViewportChange={setViewport}
                onMonkeySelect={setSelectedMonkeyId}
                onTouristSelect={setSelectedTouristId}
                hour={worldMeta.hour}
              />

              <Minimap worldMeta={worldMeta} viewport={viewport} apiBase={API_BASE} />
            </div>

            {/* Events */}
            <div className="mt-4 border border-red-500 bg-red-950/30 p-4 rounded-lg">
              <h3 className="text-red-400 text-xl font-semibold mb-3">Events</h3>

              {events.length === 0 ? (
                <div className="text-red-300">No events yet</div>
              ) : (
                <div className="flex flex-col gap-2">
                  {[...events]
                    .reverse()
                    .slice(0, 10)
                    .map((event) => (
                      <div key={event.id} className="border-b border-red-900 pb-2">
                        <span className="text-red-300">Day {event.day}</span>

                        {' · '}

                        <span className="text-white">{event.message}</span>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>

          {/* Monkey information */}
          <div>
            {selectedMonkey && (
              <div className="h-[600px] border border-white p-4 rounded-lg">
                <h3 style={{ marginTop: 0 }}>0{selectedMonkey.id}</h3>

                <div>Name: {selectedMonkey.name}</div>
                <div>Gender: {selectedMonkey.gender}</div>
                <div>Stage: {selectedMonkey.life_stage}</div>
                <div>Age: {selectedMonkey.age} days</div>
                <div>
                  Position: {selectedMonkey.x}, {selectedMonkey.y}
                </div>
                <div>Hunger: {selectedMonkey.hunger}</div>
                <div>Energy: {selectedMonkey.energy}</div>
                <div>Health: {selectedMonkey.health}/100</div>
                <div>State: {selectedMonkey.state}</div>
                <div>Target Monkey ID: {selectedMonkey.target_monkey_id}</div>

                <div>
                  <h3>Traits</h3>

                  <p>Boldness: {selectedMonkey.traits.boldness}</p>
                  <p>Curiosity: {selectedMonkey.traits.curiosity}</p>
                  <p>Sociability: {selectedMonkey.traits.sociability}</p>
                  <p>Memory: {selectedMonkey.traits.memory}</p>
                  <p>Aggression: {selectedMonkey.traits.aggression}</p>
                </div>

                <div>Status: {selectedMonkey.alive ? 'Dead' : 'Alive'}</div>

                <button
                  onClick={() => setSelectedMonkeyId(null)}
                  className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                >
                  Close
                </button>
              </div>
            )}
            {selectedTourist && (
              <div className="h-[600px] border border-white p-4 rounded-lg">
                <h3 style={{ marginTop: 0 }}>
                  Tourist {selectedTourist.id}
                </h3>

                <div>
                  Position: {selectedTourist.x}, {selectedTourist.y}
                </div>


                <div>
                  <h3>Items</h3>

                  {selectedTourist.items.length === 0 ? (
                    <div>No items</div>
                  ) : (
                    selectedTourist.items.map((item) => (
                      <div key={item.name}>
                        {item.name}
                      </div>
                    ))
                  )}
                </div>

                <button
                  onClick={() => setSelectedTouristId(null)}
                  className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
                >
                  Close
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default App