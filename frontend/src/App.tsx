import { useEffect, useMemo, useState } from 'react'

import WorldCanvas from './WorldCanvas'
import Minimap from './Minimap'

import {
  type WorldMeta,
  type Viewport,
} from './types'

import TopBar from './components/TopBar'
import PopulationPanel from './components/PopulationPanel'
import EntityInspector from './components/EntityInspector'
import EventFeed from './components/EventFeed'

import './simian-ui.css'

type SimulationStatus = {
  paused: boolean
  speed: number
  alive: number
  total: number
  deaths: number
}

export type Monkey = {
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

export type SimulationEvent = {
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

export type Tourist = {
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

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ??
  'http://127.0.0.1:8000'

function App() {
  const [worldMeta, setWorldMeta] =
    useState<WorldMeta | null>(null)

  const [viewport, setViewport] =
    useState<Viewport | null>(null)

  const [aliveMonkeys, setAliveMonkeys] =
    useState<number | null>(null)

  const [totalMonkeys, setTotalMonkeys] =
    useState<number | null>(null)

  const [monkeyDeaths, setMonkeyDeaths] =
    useState<number | null>(null)

  const [spawning, setSpawning] =
    useState(false)

  const [paused, setPaused] =
    useState<boolean | null>(null)

  const [
    simulationSpeed,
    setSimulationSpeed,
  ] = useState<number | null>(null)

  const [
    selectedMonkeyId,
    setSelectedMonkeyId,
  ] = useState<number | null>(null)

  const [
    selectedMonkey,
    setSelectedMonkey,
  ] = useState<Monkey | null>(null)

  const [
    selectedTouristId,
    setSelectedTouristId,
  ] = useState<number | null>(null)

  const [
    selectedTourist,
    setSelectedTourist,
  ] = useState<Tourist | null>(null)

  const [events, setEvents] =
    useState<SimulationEvent[]>([])

  const formatTime = (hour: number) => {
    const wholeHour =
      Math.floor(hour)

    const minutes =
      Math.floor(
        (hour - wholeHour) * 60,
      )

    return (
      `${String(wholeHour).padStart(2, '0')}:` +
      `${String(minutes).padStart(2, '0')}`
    )
  }

  useEffect(() => {
    const fetchWorldMeta = () => {
      fetch(`${API_BASE}/world/meta`)
        .then((response) => {
          if (!response.ok) {
            throw new Error(
              `HTTP ${response.status}`,
            )
          }

          return response.json()
        })
        .then((data: WorldMeta) => {
          setWorldMeta(data)
        })
        .catch((error) => {
          if (
            error instanceof DOMException &&
            error.name === 'AbortError'
          ) {
            return
          }

          console.error(
            'World meta fetch failed:',
            error,
          )
        })
    }

    fetchWorldMeta()

    const interval =
      window.setInterval(
        fetchWorldMeta,
        1000,
      )

    return () => {
      window.clearInterval(interval)
    }
  }, [])

  useEffect(() => {
    const fetchStatus = () => {
      fetch(
        `${API_BASE}/simulation/status`,
      )
        .then((response) => {
          if (!response.ok) {
            throw new Error(
              `HTTP ${response.status}`,
            )
          }

          return response.json()
        })
        .then(
          (data: SimulationStatus) => {
            setPaused(data.paused)
            setSimulationSpeed(data.speed)
            setAliveMonkeys(data.alive)
            setTotalMonkeys(data.total)
            setMonkeyDeaths(data.deaths)
          },
        )
        .catch((error) => {
          if (
            error instanceof DOMException &&
            error.name === 'AbortError'
          ) {
            return
          }

          console.error(
            'Simulation status fetch failed:',
            error,
          )
        })
    }

    fetchStatus()

    const interval =
      window.setInterval(
        fetchStatus,
        1000,
      )

    return () => {
      window.clearInterval(interval)
    }
  }, [])

  useEffect(() => {
    if (selectedMonkeyId === null) {
      setSelectedMonkey(null)
      return
    }

    const fetchSelectedMonkey = () => {
      fetch(
        `${API_BASE}/monkeys/${selectedMonkeyId}`,
      )
        .then((response) => {
          if (!response.ok) {
            throw new Error(
              `HTTP ${response.status}`,
            )
          }

          return response.json()
        })
        .then((data: Monkey) => {
          setSelectedMonkey(data)
        })
        .catch((error) => {
          if (
            error instanceof DOMException &&
            error.name === 'AbortError'
          ) {
            return
          }

          console.error(
            'Selected monkey fetch failed:',
            error,
          )
        })
    }

    fetchSelectedMonkey()

    const interval =
      window.setInterval(
        fetchSelectedMonkey,
        1000,
      )

    return () => {
      window.clearInterval(interval)
    }
  }, [selectedMonkeyId])

  useEffect(() => {
    if (selectedTouristId === null) {
      setSelectedTourist(null)
      return
    }

    const fetchSelectedTourist = () => {
      fetch(
        `${API_BASE}/tourists/${selectedTouristId}`,
      )
        .then((response) => {
          if (!response.ok) {
            throw new Error(
              `HTTP ${response.status}`,
            )
          }

          return response.json()
        })
        .then((data: Tourist) => {
          setSelectedTourist(data)
        })
        .catch((error) => {
          if (
            error instanceof DOMException &&
            error.name === 'AbortError'
          ) {
            return
          }

          console.error(
            'Selected tourist fetch failed:',
            error,
          )
        })
    }

    fetchSelectedTourist()

    const interval =
      window.setInterval(
        fetchSelectedTourist,
        1000,
      )

    return () => {
      window.clearInterval(interval)
    }
  }, [selectedTouristId])

  useEffect(() => {
    const fetchEvents = () => {
      fetch(`${API_BASE}/events`)
        .then((response) => {
          if (!response.ok) {
            throw new Error(
              `HTTP ${response.status}`,
            )
          }

          return response.json()
        })
        .then(
          (data: SimulationEvent[]) => {
            setEvents(
              Array.isArray(data)
                ? data
                : [],
            )
          },
        )
        .catch((error) => {
          if (
            error instanceof DOMException &&
            error.name === 'AbortError'
          ) {
            return
          }

          console.error(
            'Events fetch failed:',
            error,
          )
        })
    }

    fetchEvents()

    const interval =
      window.setInterval(
        fetchEvents,
        1000,
      )

    return () => {
      window.clearInterval(interval)
    }
  }, [])

  const handleSpawnMonkey = () => {
    setSpawning(true)

    fetch(
      `${API_BASE}/monkeys/spawn`,
      {
        method: 'POST',
      },
    )
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            `HTTP ${response.status}`,
          )
        }

        return response.json()
      })
      .catch((error) => {
        console.error(
          'Spawn monkey failed:',
          error,
        )
      })
      .finally(() => {
        setSpawning(false)
      })
  }

  const handlePauseToggle = async () => {
    if (paused === null) {
      return
    }

    const endpoint =
      paused
        ? '/simulation/resume'
        : '/simulation/pause'

    try {
      const response =
        await fetch(
          `${API_BASE}${endpoint}`,
          {
            method: 'POST',
          },
        )

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}`,
        )
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

  const handleSpeedChange = async (
    speed: number,
  ) => {
    try {
      const response =
        await fetch(
          `${API_BASE}/simulation/speed/${speed}`,
          {
            method: 'POST',
          },
        )

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}`,
        )
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

  const latestEvents =
    useMemo(() => {
      return [...events].sort(
        (a, b) =>
          b.tick - a.tick,
      )
    }, [events])

  if (!worldMeta) {
    return (
      <div className="simian-loading">
        <div className="simian-loading__mark">
          🐒
        </div>

        <div>
          Loading Project Simian...
        </div>
      </div>
    )
  }

  return (
    <div className="simian-app">
      <TopBar
        day={worldMeta.day}
        formattedTime={
          formatTime(worldMeta.hour)
        }
        isDaytime={
          worldMeta.isDaytime
        }
        paused={paused}
        simulationSpeed={
          simulationSpeed
        }
        events={latestEvents}
        onPauseToggle={
          handlePauseToggle
        }
        onSpeedChange={
          handleSpeedChange
        }
      />

      <main className="simian-main">
        <PopulationPanel
          alive={aliveMonkeys}
          deaths={monkeyDeaths}
          total={totalMonkeys}
          spawning={spawning}
          onSpawnMonkey={
            handleSpawnMonkey
          }
        />

        <section className="world-shell">
          <div className="world-shell__viewport">
            <div className="world-canvas-frame">
              <WorldCanvas
                worldMeta={worldMeta}
                apiBase={API_BASE}
                onViewportChange={
                  setViewport
                }
                onMonkeySelect={
                  setSelectedMonkeyId
                }
                onTouristSelect={
                  setSelectedTouristId
                }
                hour={worldMeta.hour}
              />

              <div className="world-shell__minimap">
                <div className="world-shell__overlay-label">
                  MINIMAP
                </div>

                <Minimap
                  worldMeta={worldMeta}
                  viewport={viewport}
                  apiBase={API_BASE}
                />
              </div>

              <div className="world-shell__status">
                Day {worldMeta.day}
                {' · '}
                {formatTime(
                  worldMeta.hour,
                )}
              </div>
            </div>
          </div>
        </section>

        <EntityInspector
          monkey={selectedMonkey}
          tourist={selectedTourist}
          onCloseMonkey={() =>
            setSelectedMonkeyId(
              null,
            )
          }
          onCloseTourist={() =>
            setSelectedTouristId(
              null,
            )
          }
        />
      </main>

      <EventFeed
        events={latestEvents}
      />
    </div>
  )
}

export default App