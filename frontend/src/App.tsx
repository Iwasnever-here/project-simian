import { useEffect, useState } from 'react'
import WorldCanvas from './WorldCanvas'
import Minimap from './Minimap'

type WorldMeta = {
  width: number
  height: number
  chunkSize: number
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

const API_BASE = 'http://127.0.0.1:8000'

function App() {
  const [worldMeta, setWorldMeta] = useState<WorldMeta | null>(null)
  const [viewport, setViewport] = useState<Viewport | null>(null)
  const [monkeyCount, setMonkeyCount] = useState<number | null>(null)
  const [spawning, setSpawning] = useState(false)

const [paused, setPaused] = useState<boolean | null>(null)
const [simulationSpeed, setSimulationSpeed] = useState<number | null>(null)

  useEffect(() => {
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
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}
    >
      <h1>Project Simian</h1>

      <div
        style={{
          marginBottom: 12,
          display: 'flex',
          gap: 8,
          alignItems: 'center',
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

      {worldMeta && (
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
          />

          <Minimap
            worldMeta={worldMeta}
            viewport={viewport}
            apiBase={API_BASE}
          />
        </div>
      )}
    </div>
  )
}

export default App