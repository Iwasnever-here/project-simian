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
}

type Monkey = {
  id: number
  x: number
  y: number
  hunger: number
  age: number
  energy: number
  state: string
}




const API_BASE = 'http://127.0.0.1:8000'

function App() {
  const [worldMeta, setWorldMeta] = useState<WorldMeta | null>(null)
  const [viewport, setViewport] = useState<Viewport | null>(null)
  const [monkeyCount, setMonkeyCount] = useState<number | null>(null)
  const [spawning, setSpawning] = useState(false)

const [paused, setPaused] = useState<boolean | null>(null)
const [simulationSpeed, setSimulationSpeed] = useState<number | null>(null)

const [selectedMonkeyId, setSelectedMonkeyId] = useState<number | null>(null)

const [selectedMonkey, setSelectedMonkey] = useState<Monkey | null>(null)

const formatTime = (hour: number) => {
  const wholeHour = Math.floor(hour)
  const minutes = Math.floor(
    (hour - wholeHour) * 60,
  )

  return `${String(wholeHour).padStart(2, '0')}:${String(
    minutes,
  ).padStart(2, '0')}`
}

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
          console.error(
            'World meta fetch failed:',
            error,
          )
        })
    }

    fetchWorldMeta()

    const interval = window.setInterval(
      fetchWorldMeta,
      1000,
    )

    return () => {
      window.clearInterval(interval)
    }
  }, [])

  useEffect(() => {
    fetch(`${API_BASE}/monkeys`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then((monkeys: unknown[]) => {
        setMonkeyCount(monkeys.length)
      })
      .catch((error) => {
        console.error('Monkey list fetch failed:', error)
      })
  }, [])

  useEffect(() => {
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
    })
    .catch((error) => {
      console.error(
        'Simulation status fetch failed:',
        error,
      )
    })
}, [])

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
        console.error(
          'Selected monkey fetch failed:',
          error,
        )
      })
  }

  fetchSelectedMonkey()

  const interval = window.setInterval(
    fetchSelectedMonkey,
    1000,
  )

  return () => {
    window.clearInterval(interval)
  }
}, [selectedMonkeyId])

  const handleSpawnMonkey = () => {
    setSpawning(true)

    fetch(`${API_BASE}/monkeys/spawn`, {
      method: 'POST',
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        return response.json()
      })
      .then(() => {
        setMonkeyCount((count) => (count ?? 0) + 1)
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

    const endpoint = paused
      ? '/simulation/resume'
      : '/simulation/pause'

    try {
      const response = await fetch(
        `${API_BASE}${endpoint}`,
        {
          method: 'POST',
        },
      )

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: SimulationStatus =
        await response.json()

      setPaused(data.paused)
      setSimulationSpeed(data.speed)
    } catch (error) {
      console.error(
        'Simulation pause/resume failed:',
        error,
      )
    }
  }

  const handleSpeedChange = async (speed: number) => {
    try {
      const response = await fetch(
        `${API_BASE}/simulation/speed/${speed}`,
        {
          method: 'POST',
        },
      )

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: SimulationStatus =
        await response.json()

      setPaused(data.paused)
      setSimulationSpeed(data.speed)
    } catch (error) {
      console.error(
        'Simulation speed change failed:',
        error,
      )
    }
  }

  const handleSingleTick = async () => {
    try {
      const response = await fetch(
        `${API_BASE}/simulation/tick`,
        {
          method: 'POST',
        },
      )

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
    } catch (error) {
      console.error(
        'Simulation tick failed:',
        error,
      )
    }
  }

  return (
  <div
    style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
    }}
  >
    {/* Top bar */}
    <div
      style={{
        width: 'min(1400px, 95vw)',
        display: 'grid',
        gridTemplateColumns: '1fr auto 1fr',
        alignItems: 'center',
        padding: '16px 0',
      }}
    >
      {/* Left - world time */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-start',
        }}
      >
        {worldMeta && (
          <span
            style={{
              fontSize: 18,
            }}
          >
            Day {worldMeta.day} · {formatTime(worldMeta.hour)}
            {' '}
            {worldMeta.isDaytime ? '☀️' : '🌙'}
          </span>
        )}
      </div>

      {/* Centre - title */}
      <h1
        style={{
          margin: 0,
          fontSize: 42,
        }}
      >
        Project Simian
      </h1>

      {/* Right - simulation controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <button
          onClick={handleSpawnMonkey}
          disabled={spawning}
        >
          {spawning ? 'Spawning...' : 'Spawn Monkey'}
        </button>

        <span>
          Monkeys: {monkeyCount ?? '...'}
        </span>

        <button
          onClick={handlePauseToggle}
          disabled={paused === null}
        >
          {paused === null
            ? 'Loading...'
            : paused
              ? '▶ Resume'
              : '⏸ Pause'}
        </button>

        {[0.5, 1, 2, 4].map((speed) => (
          <button
            key={speed}
            onClick={() => handleSpeedChange(speed)}
            disabled={
              simulationSpeed === null ||
              simulationSpeed === speed
            }
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
          gridTemplateColumns: '240px 800px 240px',
          gap: 24,
          alignItems: 'start',
        }}
      >
        {/* Empty left column keeps map centred */}
        <div />

        {/* World */}
        <div
          style={{
            position: 'relative',
            width: 800,
            height: 600,
          }}
        >
          <WorldCanvas
            worldMeta={worldMeta}
            apiBase={API_BASE}
            onViewportChange={setViewport}
            onMonkeySelect={setSelectedMonkeyId}
          />

          <Minimap
            worldMeta={worldMeta}
            viewport={viewport}
            apiBase={API_BASE}
          />
        </div>

        {/* Monkey information */}
        <div>
          {selectedMonkey && (
            <div
              style={{
                padding: 16,
                width: 220,
                border: '1px solid #cccccc',
                borderRadius: 8,
              }}
            >
              <h3
                style={{
                  marginTop: 0,
                }}
              >
                Monkey 0{selectedMonkey.id}
              </h3>

              <div>
                Age: {selectedMonkey.age} days
              </div>

              <div>
                Position: {selectedMonkey.x}, {selectedMonkey.y}
              </div>

              <div>
                Hunger: {selectedMonkey.hunger}
              </div>

              <div>
                Energy: {selectedMonkey.energy}
              </div>

              <div>
                State: {selectedMonkey.state}
              </div>

              <button
                onClick={() => setSelectedMonkeyId(null)}
                style={{
                  marginTop: 12,
                }}
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