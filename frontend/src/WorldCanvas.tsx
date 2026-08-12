import { Application, extend } from '@pixi/react'
import {
  Container,
  Graphics,
  Sprite,
  Texture,
  FederatedPointerEvent,
} from 'pixi.js'
import { useCallback, useEffect, useRef, useState } from 'react'

extend({ Container, Graphics, Sprite })

type WorldMeta = {
  width: number
  height: number
  chunkSize: number
}

type WorldCanvasProps = {
  worldMeta: WorldMeta
  apiBase: string
  onViewportChange?: (viewport: { x: number; y: number; width: number; height: number }) => void
}

type TreeData = {
  x: number
  y: number
  species: string
}

type MonkeyData = {
  id: number
  x: number
  y: number
  hunger: number
  state: string
  target: { x: number; y: number } | null
}

type ChunkResponse = {
  cx: number
  cy: number
  w: number
  h: number
  terrain: string
  trees: TreeData[]
}

type LoadedChunk = {
  texture: Texture
  trees: TreeData[]
  width: number
  height: number
}

const TILE_SIZE = 8

const VIEWPORT_WIDTH = 800
const VIEWPORT_HEIGHT = 600

const LOAD_MARGIN_CHUNKS = 1
const MONKEY_POLL_INTERVAL = 1000

const TERRAIN_COLOR: Record<string, [number, number, number]> = {
  w: [30, 144, 255],
  s: [245, 222, 179],
  g: [124, 168, 78],
  f: [34, 92, 45],
  m: [90, 110, 70],
  r: [120, 110, 100],
  n: [240, 245, 250],
}

function chunkKey(cx: number, cy: number) {
  return `${cx}:${cy}`
}

function WorldCanvas({ worldMeta, apiBase, onViewportChange }: WorldCanvasProps) {
  const { width, height, chunkSize } = worldMeta

  const chunkPixelSize = chunkSize * TILE_SIZE

  const cameraRef = useRef({ x: 0, y: 0 })
  const containerRef = useRef<any>(null)
  const lastPointerRef = useRef({ x: 0, y: 0 })
  const chunksRef = useRef<Map<string, LoadedChunk>>(new Map())
  const loadingRef = useRef<Set<string>>(new Set())

  const [dragging, setDragging] = useState(false)
  const [monkeys, setMonkeys] = useState<MonkeyData[]>([])
  const [selectedMonkeyId, setSelectedMonkeyId] = useState<number | null>(null)
  const [, bumpVersion] = useState(0)

  const forceRender = useCallback(() => {
    bumpVersion((version) => version + 1)
  }, [])

  const loadChunk = useCallback(
    async (cx: number, cy: number) => {
      const key = chunkKey(cx, cy)

      if (chunksRef.current.has(key) || loadingRef.current.has(key)) {
        return
      }

      loadingRef.current.add(key)

      try {
        const response = await fetch(`${apiBase}/world/chunk/${cx}/${cy}`)

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const data: ChunkResponse = await response.json()

        const canvas = document.createElement('canvas')
        canvas.width = data.w
        canvas.height = data.h

        const context = canvas.getContext('2d')

        if (!context) {
          throw new Error('2D context unavailable')
        }

        const imageData = context.createImageData(data.w, data.h)

        for (let i = 0; i < data.terrain.length; i++) {
          const [r, g, b] = TERRAIN_COLOR[data.terrain[i]] ?? [0, 0, 0]
          const pixelIndex = i * 4

          imageData.data[pixelIndex] = r
          imageData.data[pixelIndex + 1] = g
          imageData.data[pixelIndex + 2] = b
          imageData.data[pixelIndex + 3] = 255
        }

        context.putImageData(imageData, 0, 0)

        const texture = Texture.from(canvas)
        texture.source.scaleMode = 'nearest'

        chunksRef.current.set(key, {
          texture,
          trees: data.trees ?? [],
          width: data.w,
          height: data.h,
        })
      } catch (error) {
        console.error(`Chunk fetch failed (${cx}, ${cy}):`, error)
      } finally {
        loadingRef.current.delete(key)
        forceRender()
      }
    },
    [apiBase, forceRender],
  )

  const loadMonkeys = useCallback(async () => {
    try {
      const response = await fetch(
        `${apiBase}/monkeys`,
      )

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}`,
        )
      }

      const data: MonkeyData[] =
        await response.json()

      setMonkeys(data)
    } catch (error) {
      console.error(
        'Monkey fetch failed:',
        error,
      )
    }
  }, [apiBase])

  useEffect(() => {
    loadMonkeys()

    const interval = window.setInterval(loadMonkeys, MONKEY_POLL_INTERVAL)

    return () => {
      window.clearInterval(interval)
    }
  }, [loadMonkeys])

  const selectedMonkey =
    selectedMonkeyId === null
      ? null
      : monkeys.find((monkey) => monkey.id === selectedMonkeyId) ?? null

  const maxCx = Math.ceil(width / chunkSize) - 1
  const maxCy = Math.ceil(height / chunkSize) - 1

  const updateVisibleChunks = useCallback(() => {
    const { x: cameraX, y: cameraY } = cameraRef.current

    const startCx = Math.max(
      0,
      Math.floor(-cameraX / chunkPixelSize) - LOAD_MARGIN_CHUNKS,
    )

    const endCx = Math.min(
      maxCx,
      Math.floor((-cameraX + VIEWPORT_WIDTH) / chunkPixelSize) + LOAD_MARGIN_CHUNKS,
    )

    const startCy = Math.max(
      0,
      Math.floor(-cameraY / chunkPixelSize) - LOAD_MARGIN_CHUNKS,
    )

    const endCy = Math.min(
      maxCy,
      Math.floor((-cameraY + VIEWPORT_HEIGHT) / chunkPixelSize) + LOAD_MARGIN_CHUNKS,
    )

    for (let cy = startCy; cy <= endCy; cy++) {
      for (let cx = startCx; cx <= endCx; cx++) {
        loadChunk(cx, cy)
      }
    }

    onViewportChange?.({
      x: -cameraX / TILE_SIZE,
      y: -cameraY / TILE_SIZE,
      width: VIEWPORT_WIDTH / TILE_SIZE,
      height: VIEWPORT_HEIGHT / TILE_SIZE,
    })
  }, [chunkPixelSize, maxCx, maxCy, loadChunk, onViewportChange])

  useEffect(() => {
    updateVisibleChunks()
  }, [updateVisibleChunks])

  const throttleRef = useRef<number | null>(null)

  const scheduleViewUpdate = useCallback(() => {
    if (throttleRef.current !== null) {
      return
    }

    throttleRef.current = window.setTimeout(() => {
      throttleRef.current = null
      updateVisibleChunks()
    }, 150)
  }, [updateVisibleChunks])

  useEffect(() => {
    return () => {
      if (throttleRef.current !== null) {
        window.clearTimeout(throttleRef.current)
      }

      for (const chunk of chunksRef.current.values()) {
        chunk.texture.destroy(true)
      }

      chunksRef.current.clear()
    }
  }, [])

  const handleWorldClick = useCallback(
    (event: FederatedPointerEvent) => {
      const worldPixelX = event.global.x - cameraRef.current.x
      const worldPixelY = event.global.y - cameraRef.current.y

      const tileX = Math.floor(worldPixelX / TILE_SIZE)
      const tileY = Math.floor(worldPixelY / TILE_SIZE)

      const monkey = monkeys.find(
        (candidate) => candidate.x === tileX && candidate.y === tileY,
      )

      setSelectedMonkeyId(monkey?.id ?? null)
    },
    [monkeys],
  )

  const loadedChunks = Array.from(chunksRef.current.entries())

  return (
    <div>
      <Application width={VIEWPORT_WIDTH} height={VIEWPORT_HEIGHT} backgroundColor={0x1e90ff}>
        <pixiContainer ref={containerRef}>
          {loadedChunks.map(([key, chunk]) => {
            const [cx, cy] = key.split(':').map(Number)

            return (
              <pixiContainer key={key} x={cx * chunkPixelSize} y={cy * chunkPixelSize}>
                <pixiSprite
                  texture={chunk.texture}
                  x={0}
                  y={0}
                  width={chunk.width * TILE_SIZE}
                  height={chunk.height * TILE_SIZE}
                />

                <pixiGraphics
                  draw={(graphics) => {
                    graphics.clear()

                    for (const tree of chunk.trees) {
                      const treeX = tree.x * TILE_SIZE
                      const treeY = tree.y * TILE_SIZE

                      graphics.rect(treeX + 3, treeY + 4, 2, 4).fill(0x6b4423)
                      graphics.rect(treeX + 1, treeY + 1, 6, 5).fill(0x123d1f)
                    }
                  }}
                />
              </pixiContainer>
            )
          })}

          {/* All monkeys are drawn in one batch. */}
          <pixiGraphics
            draw={(graphics) => {
              graphics.clear()

              for (const monkey of monkeys) {
                const monkeyX = monkey.x * TILE_SIZE
                const monkeyY = monkey.y * TILE_SIZE
                const selected = monkey.id === selectedMonkeyId

                graphics
                  .rect(monkeyX, monkeyY, TILE_SIZE * 2, TILE_SIZE * 2)
                  .fill(0x6b4423)
              }
            }}
          />
        </pixiContainer>

        <pixiGraphics
          eventMode="static"
          cursor={dragging ? 'grabbing' : 'grab'}
          draw={(graphics) => {
            graphics.clear()

            graphics
              .rect(0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
              .fill({ color: 0x000000, alpha: 0 })
          }}
          onPointerDown={(event: FederatedPointerEvent) => {
            setDragging(true)
            lastPointerRef.current = { x: event.global.x, y: event.global.y }
          }}
          onPointerMove={(event: FederatedPointerEvent) => {
            if (!dragging) {
              return
            }

            const currentX = event.global.x
            const currentY = event.global.y

            const dx = currentX - lastPointerRef.current.x
            const dy = currentY - lastPointerRef.current.y

            cameraRef.current.x += dx
            cameraRef.current.y += dy

            if (containerRef.current) {
              containerRef.current.x = cameraRef.current.x
              containerRef.current.y = cameraRef.current.y
            }

            lastPointerRef.current = { x: currentX, y: currentY }

            scheduleViewUpdate()
          }}
          onPointerUp={(event: FederatedPointerEvent) => {
            setDragging(false)

            const movementX = Math.abs(event.global.x - lastPointerRef.current.x)
            const movementY = Math.abs(event.global.y - lastPointerRef.current.y)

            if (movementX < 3 && movementY < 3) {
              handleWorldClick(event)
            }

            updateVisibleChunks()
          }}
          onPointerUpOutside={() => {
            setDragging(false)
            updateVisibleChunks()
          }}
        />
      </Application>

      {selectedMonkey && (
        <div
          style={{
            marginTop: 12,
            padding: 12,
            width: 220,
            border: '1px solid #cccccc',
            borderRadius: 8,
          }}
        >
          <strong>Monkey #{selectedMonkey.id}</strong>

          <div>
            Position: {selectedMonkey.x}, {selectedMonkey.y}
          </div>

          <div>Hunger: {selectedMonkey.hunger}</div>

          <div>State: {selectedMonkey.state}</div>

          {selectedMonkey.target && (
            <div>
              Target: {selectedMonkey.target.x}, {selectedMonkey.target.y}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default WorldCanvas
