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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <h1>Project Simian</h1>

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
