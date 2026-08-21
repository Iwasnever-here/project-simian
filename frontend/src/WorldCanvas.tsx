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

type Viewport = {
  x: number
  y: number
  width: number
  height: number
}

type WorldCanvasProps = {
  worldMeta: WorldMeta
  apiBase: string
  onViewportChange?: (viewport: Viewport) => void
  onMonkeySelect?: (monkeyId: number | null) => void
  hour: number
}

type TreeData = {
  x: number
  y: number
  species: string
}

type TempleData = {
  x: number
  y: number
  width: number
  height: number
  entrance: {
    x: number
    y: number
  }
}

type MonkeyData = {
  id: number
  x: number
  y: number
  hunger: number
  energy: number
  life_stage: string
  age: number
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

const VIEWPORT_WIDTH = 900
const VIEWPORT_HEIGHT = 600

const LOAD_MARGIN_CHUNKS = 1
const MONKEY_POLL_INTERVAL = 1000

const MIN_ZOOM = 0.5
const MAX_ZOOM = 4
const ZOOM_SPEED = 0.0015

const TERRAIN_COLOR: Record<string, [number, number, number]> = {
  w: [100, 149, 237],
  s: [245, 222, 179],
  g: [110, 139, 61],
  f: [74, 93, 35],
  m: [85, 93, 80],
  r: [120, 110, 100],
  n: [240, 245, 250],
}

function getMonkeyScale(lifeStage: string) {
  if (lifeStage === 'infant') {
    return 0.5
  }

  if (lifeStage === 'juvenile') {
    return 0.75
  }

  return 1
}

function chunkKey(cx: number, cy: number) {
  return `${cx}:${cy}`
}

function WorldCanvas({
  worldMeta,
  apiBase,
  onViewportChange,
  onMonkeySelect,
  hour,
}: WorldCanvasProps) {
  const { width, height, chunkSize } = worldMeta

  const chunkPixelSize = chunkSize * TILE_SIZE

  const cameraRef = useRef({ x: 0, y: 0, zoom: 1 })
  const containerRef = useRef<any>(null)
  const wrapperRef = useRef<HTMLDivElement | null>(null)
  const lastPointerRef = useRef({ x: 0, y: 0 })
  const pointerDownRef = useRef({ x: 0, y: 0 })
  const chunksRef = useRef<Map<string, LoadedChunk>>(new Map())
  const loadingRef = useRef<Set<string>>(new Set())
  const throttleRef = useRef<number | null>(null)

  const [dragging, setDragging] = useState(false)
  const [zoom, setZoom] = useState(1)
  const [monkeys, setMonkeys] = useState<MonkeyData[]>([])
  const [temple, setTemple] = useState<TempleData | null>(null)

  const [, bumpVersion] = useState(0)
  const nightAlpha = getNightAlpha(hour)

  function getNightAlpha(hour: number) {
    // Full daylight: 08:00 - 17:00
    if (hour >= 8 && hour < 17) {
      return 0
    }

    // Sunset: 17:00 - 20:00
    if (hour >= 17 && hour < 20) {
      const progress = (hour - 17) / 3
      return progress * 0.5
    }

    // Full night: 20:00 - 05:00
    if (hour >= 20 || hour < 5) {
      return 0.5
    }

    // Sunrise: 05:00 - 08:00
    const progress = (hour - 5) / 3

    return 0.5 * (1 - progress)
  }

  const forceRender = useCallback(() => {
    bumpVersion((version) => version + 1)
  }, [])

  const maxCx = Math.ceil(width / chunkSize) - 1
  const maxCy = Math.ceil(height / chunkSize) - 1

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

  const loadTemple = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/temple`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: TempleData = await response.json()
      setTemple(data)
    } catch (error) {
      console.error('Temple fetch failed:', error)
    }
  }, [apiBase])

  const loadMonkeys = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/monkeys`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: MonkeyData[] = await response.json()
      setMonkeys(data)
    } catch (error) {
      console.error('Monkey fetch failed:', error)
    }
  }, [apiBase])

  useEffect(() => {
    loadMonkeys()

    const interval = window.setInterval(loadMonkeys, MONKEY_POLL_INTERVAL)

    return () => {
      window.clearInterval(interval)
    }
  }, [loadMonkeys])

  useEffect(() => {
    loadTemple()
  }, [loadTemple])

  const updateVisibleChunks = useCallback(() => {
    const { x: cameraX, y: cameraY, zoom: cameraZoom } = cameraRef.current

    /*
     * Convert the visible screen area back into world pixel coordinates.
     */
    const worldLeft = -cameraX / cameraZoom
    const worldTop = -cameraY / cameraZoom
    const worldRight = (VIEWPORT_WIDTH - cameraX) / cameraZoom
    const worldBottom = (VIEWPORT_HEIGHT - cameraY) / cameraZoom

    const startCx = Math.max(
      0,
      Math.floor(worldLeft / chunkPixelSize) - LOAD_MARGIN_CHUNKS,
    )

    const endCx = Math.min(
      maxCx,
      Math.floor(worldRight / chunkPixelSize) + LOAD_MARGIN_CHUNKS,
    )

    const startCy = Math.max(
      0,
      Math.floor(worldTop / chunkPixelSize) - LOAD_MARGIN_CHUNKS,
    )

    const endCy = Math.min(
      maxCy,
      Math.floor(worldBottom / chunkPixelSize) + LOAD_MARGIN_CHUNKS,
    )

    for (let cy = startCy; cy <= endCy; cy++) {
      for (let cx = startCx; cx <= endCx; cx++) {
        loadChunk(cx, cy)
      }
    }

    /*
     * This is also what keeps the minimap viewport correct.
     */
    onViewportChange?.({
      x: worldLeft / TILE_SIZE,
      y: worldTop / TILE_SIZE,
      width: VIEWPORT_WIDTH / (TILE_SIZE * cameraZoom),
      height: VIEWPORT_HEIGHT / (TILE_SIZE * cameraZoom),
    })
  }, [chunkPixelSize, maxCx, maxCy, loadChunk, onViewportChange])

  useEffect(() => {
    updateVisibleChunks()
  }, [updateVisibleChunks])

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
      const camera = cameraRef.current

      const worldPixelX = (event.global.x - camera.x) / camera.zoom
      const worldPixelY = (event.global.y - camera.y) / camera.zoom

      const tileX = Math.floor(worldPixelX / TILE_SIZE)
      const tileY = Math.floor(worldPixelY / TILE_SIZE)

      const monkey = monkeys.find(
        (candidate) => candidate.x === tileX && candidate.y === tileY,
      )

      onMonkeySelect?.(monkey?.id ?? null)
    },
    [monkeys, onMonkeySelect],
  )

  /*
   * React's onWheel is registered as a passive listener, so
   * event.preventDefault() inside it is silently ignored and the page
   * scrolls underneath the canvas while we also try to zoom. Attaching
   * a native listener with { passive: false } lets us actually cancel
   * the scroll, so zooming over the world doesn't scroll the page.
   */
  useEffect(() => {
    const element = wrapperRef.current

    if (!element) {
      return
    }

    const handleWheel = (event: WheelEvent) => {
      event.preventDefault()

      const rect = element.getBoundingClientRect()
      const mouseX = event.clientX - rect.left
      const mouseY = event.clientY - rect.top

      const camera = cameraRef.current
      const oldZoom = camera.zoom

      const nextZoom = Math.min(
        MAX_ZOOM,
        Math.max(MIN_ZOOM, oldZoom * Math.exp(-event.deltaY * ZOOM_SPEED)),
      )

      if (nextZoom === oldZoom) {
        return
      }

      /*
       * Find the world position underneath the cursor before zooming.
       */
      const worldX = (mouseX - camera.x) / oldZoom
      const worldY = (mouseY - camera.y) / oldZoom

      /*
       * Move camera so that world position stays underneath cursor.
       */
      camera.x = mouseX - worldX * nextZoom
      camera.y = mouseY - worldY * nextZoom
      camera.zoom = nextZoom

      if (containerRef.current) {
        containerRef.current.x = camera.x
        containerRef.current.y = camera.y
        containerRef.current.scale.set(nextZoom)
      }

      setZoom(nextZoom)

      scheduleViewUpdate()
    }

    element.addEventListener('wheel', handleWheel, { passive: false })

    return () => {
      element.removeEventListener('wheel', handleWheel)
    }
  }, [scheduleViewUpdate])

  const loadedChunks = Array.from(chunksRef.current.entries())

  return (
    <div>
      <div
        ref={wrapperRef}
        style={{ position: 'relative', width: VIEWPORT_WIDTH, height: VIEWPORT_HEIGHT }}
      >
        <Application width={VIEWPORT_WIDTH} height={VIEWPORT_HEIGHT} backgroundColor={0x6495ed}>
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

            {temple && (
              <pixiGraphics
                draw={(graphics) => {
                  graphics.clear()

                  const x = temple.x * TILE_SIZE
                  const y = temple.y * TILE_SIZE

                  const width = temple.width * TILE_SIZE
                  const height = temple.height * TILE_SIZE

                  const wallThickness = TILE_SIZE * 1.5
                  const towerRadius = TILE_SIZE * 1.8

                  const entranceWidth = TILE_SIZE * 2

                  // Outer platform
                  graphics
                    .rect(
                      x - TILE_SIZE,
                      y - TILE_SIZE,
                      width + TILE_SIZE * 2,
                      height + TILE_SIZE * 2,
                    )
                    .fill(0x9f9270)

                  // Main temple floor
                  graphics.rect(x, y, width, height).fill(0xc2b280)

                  // Inner courtyard
                  graphics
                    .rect(
                      x + wallThickness,
                      y + wallThickness,
                      width - wallThickness * 2,
                      height - wallThickness * 2,
                    )
                    .fill(0xd6c69c)

                  // Top wall
                  graphics.rect(x, y, width, wallThickness).fill(0x6b6045)

                  // Left wall
                  graphics.rect(x, y, wallThickness, height).fill(0x6b6045)

                  // Right wall
                  graphics
                    .rect(x + width - wallThickness, y, wallThickness, height)
                    .fill(0x6b6045)

                  // Bottom wall left section
                  graphics
                    .rect(
                      x,
                      y + height - wallThickness,
                      width / 2 - entranceWidth / 2,
                      wallThickness,
                    )
                    .fill(0x6b6045)

                  // Bottom wall right section
                  graphics
                    .rect(
                      x + width / 2 + entranceWidth / 2,
                      y + height - wallThickness,
                      width / 2 - entranceWidth / 2,
                      wallThickness,
                    )
                    .fill(0x6b6045)

                  // Corner towers
                  graphics.circle(x, y, towerRadius).fill(0x786b4d)
                  graphics.circle(x + width, y, towerRadius).fill(0x786b4d)
                  graphics.circle(x, y + height, towerRadius).fill(0x786b4d)
                  graphics
                    .circle(x + width, y + height, towerRadius)
                    .fill(0x786b4d)

                  // Entrance
                  const entranceX = temple.entrance.x * TILE_SIZE
                  const entranceY = temple.entrance.y * TILE_SIZE

                  graphics
                    .rect(entranceX - TILE_SIZE / 2, entranceY, entranceWidth, TILE_SIZE)
                    .fill(0x3b2a1f)

                  // Central shrine
                  graphics
                    .circle(x + width / 2, y + height / 2, TILE_SIZE * 0.8)
                    .fill(0x8f7d52)
                }}
              />
            )}

            <pixiGraphics
              draw={(graphics) => {
                graphics.clear()

                for (const monkey of monkeys) {
                  const scale = getMonkeyScale(monkey.life_stage)

                  const monkeyX = monkey.x * TILE_SIZE
                  const monkeyY = monkey.y * TILE_SIZE

                  const centerX = monkeyX + TILE_SIZE
                  const baseY = monkeyY + TILE_SIZE * 2

                  const bodyRadius = TILE_SIZE * 0.7 * scale
                  const headRadius = TILE_SIZE * 0.5 * scale
                  const earRadius = TILE_SIZE * 0.2 * scale

                  const bodyCenterY = baseY - bodyRadius
                  const headCenterY =
                    bodyCenterY -
                    bodyRadius -
                    headRadius * 0.5

                  graphics
                    .circle(
                      centerX,
                      bodyCenterY,
                      bodyRadius,
                    )
                    .fill(0x6b4423)

                  graphics
                    .circle(
                      centerX,
                      headCenterY,
                      headRadius,
                    )
                    .fill(0x7a5230)

                  graphics
                    .circle(
                      centerX - headRadius,
                      headCenterY,
                      earRadius,
                    )
                    .fill(0x7a5230)

                  graphics
                    .circle(
                      centerX + headRadius,
                      headCenterY,
                      earRadius,
                    )
                    .fill(0x7a5230)
                }
              }}
            />
          </pixiContainer>

          {nightAlpha > 0 && (
            <pixiGraphics
              draw={(graphics) => {
                graphics.clear()

                graphics
                  .rect(0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
                  .fill({ color: 0x08111f, alpha: nightAlpha })
              }}
            />
          )}

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

              const point = { x: event.global.x, y: event.global.y }

              lastPointerRef.current = point
              pointerDownRef.current = point
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

              const movementX = Math.abs(event.global.x - pointerDownRef.current.x)
              const movementY = Math.abs(event.global.y - pointerDownRef.current.y)

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
      </div>

      <div style={{ marginTop: 8, fontSize: 14 }}>
        Zoom: {Math.round(zoom * 100)}%
      </div>
    </div>
  )
}

export default WorldCanvas