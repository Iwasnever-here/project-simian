import { Application, extend } from '@pixi/react'
import { Graphics } from 'pixi.js'

extend({
  Graphics,
})

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

type WorldCanvasProps = {
  world: World
}

const TILE_SIZE = 24

function WorldCanvas({ world }: WorldCanvasProps) {
  return (
    <Application
      width={world.width * TILE_SIZE}
      height={world.height * TILE_SIZE}
      backgroundColor={0x222222}
    >
      {world.tiles.map((tile) => (
        <pixiGraphics
          key={`${tile.x}-${tile.y}`}
          draw={(graphics) => {
            graphics.clear()

            graphics
              .rect(
                tile.x * TILE_SIZE,
                tile.y * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE,
              )
              .fill(0x4f8f3a)
          }}
        />
      ))}
    </Application>
  )
}

export default WorldCanvas