import { useEffect, useState } from 'react'
import WorldCanvas from './WorldCanvas'

type Tile = {
  x: number
  y: number
  terrain: string
}

type World = {
  width: number
  height: number
  tiles: Tile[]
}

function App() {
  const [world, setWorld] = useState<World | null>(null)

  useEffect(() => {
    fetch('http://127.0.0.1:8000/world')
      .then((response) => response.json())
      .then((data: World) => setWorld(data))
  }, [])

  return (
    <div>
      <h1>Simian Engine</h1>

      {world && <WorldCanvas world={world} />}
    </div>
  )
}

export default App