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

const API_BASE = 'http://127.0.0.1:8000'

function App() {
  const [worldMeta, setWorldMeta] = useState<WorldMeta | null>(null)
  const [viewport, setViewport] = useState<Viewport | null>(null)
  const [monkeyCount, setMonkeyCount] = useState<number | null>(null)
  const [spawning, setSpawning] = useState(false)

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
      .then((res) => res.json())
      .then((monkeys: unknown[]) => setMonkeyCount(monkeys.length))
      .catch((error) => console.error('Monkey list fetch failed:', error))
  }, [])

  const handleSpawnMonkey = () => {
    setSpawning(true)

    fetch(`${API_BASE}/monkeys/spawn`, { method: 'POST' })
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <h1>Project Simian</h1>

      <div style={{ marginBottom: 12, display: 'flex', gap: 12, alignItems: 'center' }}>
        <button onClick={handleSpawnMonkey} disabled={spawning}>
          {spawning ? 'Spawning...' : 'Spawn Monkey'}
        </button>
        <span>Monkeys: {monkeyCount ?? '...'}</span>
      </div>

      {worldMeta && (
        <div style={{ position: 'relative', width: 800, height: 600}}>
          <WorldCanvas
            worldMeta={worldMeta}
            apiBase={API_BASE}
            onViewportChange={setViewport}
          />
          <Minimap worldMeta={worldMeta} viewport={viewport} apiBase={API_BASE} />
        </div>
      )}
    </div>
  )
}

export default App
