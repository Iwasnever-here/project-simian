import { useEffect, useState } from 'react'
import WorldCanvas from './WorldCanvas'

type WorldMeta = {
  width: number
  height: number
  chunkSize: number
}

const API_BASE = 'http://127.0.0.1:8000'

function App() {
  const [worldMeta, setWorldMeta] = useState<WorldMeta | null>(null)

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
    <div>
      <h1>Simian Engine</h1>

      {worldMeta && <WorldCanvas worldMeta={worldMeta} apiBase={API_BASE} />}
    </div>
  )
}

export default App
