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

import { type WorldMeta, type Viewport, TERRAIN_COLOR } from './types'

type WorldCanvasProps = {
  worldMeta: WorldMeta
  apiBase: string
  onViewportChange?: (viewport: Viewport) => void
  onMonkeySelect?: (monkeyId: number | null) => void
  onTouristSelect?: (touristId: number | null) => void
  selectedMonkeyId: number | null
  selectedTouristId: number | null
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

type TouristData = {
  id: number
  x: number
  y: number
  state: string
  insideTemple: boolean
}

type BoatLandingData = {
  x: number
  y: number
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
const TOURIST_POLL_INTERVAL = 1000

const MIN_ZOOM = 0.5
const MAX_ZOOM = 4
const ZOOM_SPEED = 0.0015


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
  onTouristSelect,
  selectedMonkeyId,
  selectedTouristId,
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
  const [tourists, setTourists] = useState<TouristData[]>([])
  const [boatLanding, setBoatLanding] = useState<BoatLandingData | null>(null)

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

  const loadTourists = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/tourists`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: TouristData[] = await response.json()
      setTourists(data)
    } catch (error) {
      console.error('Tourist fetch failed:', error)
    }
  }, [apiBase])

  const loadBoatLanding = useCallback(async () => {
    try {
      const response = await fetch(`${apiBase}/boat-landing`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: BoatLandingData = await response.json()
      setBoatLanding(data)
    } catch (error) {
      console.error('Boat landing fetch failed:', error)
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

  useEffect(() => {
    loadTourists()

    const interval = window.setInterval(loadTourists, TOURIST_POLL_INTERVAL)

    return () => {
      window.clearInterval(interval)
    }
  }, [loadTourists])

  useEffect(() => {
    loadBoatLanding()
  }, [loadBoatLanding])

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

    const worldPixelX =
      (event.global.x - camera.x) / camera.zoom

    const worldPixelY =
      (event.global.y - camera.y) / camera.zoom

    let closestMonkey: MonkeyData | null = null
    let closestMonkeyDistance = Infinity

    for (const monkey of monkeys) {
      const scale = getMonkeyScale(
        monkey.life_stage,
      )

      const monkeyX = monkey.x * TILE_SIZE
      const monkeyY = monkey.y * TILE_SIZE

      const centerX = monkeyX + TILE_SIZE
      const centerY = monkeyY + TILE_SIZE

      const hitRadius =
        TILE_SIZE * 1.2 * scale

      const dx = worldPixelX - centerX
      const dy = worldPixelY - centerY

      const distance = Math.sqrt(
        dx * dx + dy * dy,
      )

      if (
        distance <= hitRadius &&
        distance < closestMonkeyDistance
      ) {
        closestMonkey = monkey
        closestMonkeyDistance = distance
      }
    }

    let closestTourist: TouristData | null = null
    let closestTouristDistance = Infinity

    for (const tourist of tourists) {
      if (tourist.insideTemple) {
        continue
      }

      const touristX =
        tourist.x * TILE_SIZE

      const touristY =
        tourist.y * TILE_SIZE

      const centerX =
        touristX + TILE_SIZE

      const centerY =
        touristY + TILE_SIZE

      const hitRadius =
        TILE_SIZE * 1.2

      const dx =
        worldPixelX - centerX

      const dy =
        worldPixelY - centerY

      const distance = Math.sqrt(
        dx * dx + dy * dy,
      )

      if (
        distance <= hitRadius &&
        distance < closestTouristDistance
      ) {
        closestTourist = tourist
        closestTouristDistance = distance
      }
    }

    if (
      closestMonkey &&
      (
        !closestTourist ||
        closestMonkeyDistance <=
          closestTouristDistance
      )
    ) {
      onMonkeySelect?.(
        closestMonkey.id,
      )

      onTouristSelect?.(null)

      return
    }

    if (closestTourist) {
      onTouristSelect?.(
        closestTourist.id,
      )

      onMonkeySelect?.(null)

      return
    }

    onMonkeySelect?.(null)
    onTouristSelect?.(null)
  },
  [
    monkeys,
    tourists,
    onMonkeySelect,
    onTouristSelect,
  ],
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

            {boatLanding && (
              <pixiGraphics
                draw={(graphics) => {
                  graphics.clear()

                  const x = boatLanding.x * TILE_SIZE
                  const y = boatLanding.y * TILE_SIZE

                  // Dock
                  graphics
                    .rect(
                      x - TILE_SIZE * 2,
                      y + TILE_SIZE * 4,
                      TILE_SIZE * 6,
                      TILE_SIZE * 0.8,
                    )
                    .fill(0x8b6f47)

                  // Large hull
                  graphics
                    .poly([
                      x - TILE_SIZE * 3.5, y + TILE_SIZE * 1.5,
                      x + TILE_SIZE * 4.5, y + TILE_SIZE * 1.5,

                      x + TILE_SIZE * 3.8, y + TILE_SIZE * 2.8,
                      x + TILE_SIZE * 3.0, y + TILE_SIZE * 3.6,
                      x + TILE_SIZE * 2.0, y + TILE_SIZE * 4.1,
                      x + TILE_SIZE * 0.8, y + TILE_SIZE * 4.4,

                      x - TILE_SIZE * 0.5, y + TILE_SIZE * 4.3,
                      x - TILE_SIZE * 1.6, y + TILE_SIZE * 3.9,
                      x - TILE_SIZE * 2.5, y + TILE_SIZE * 3.2,
                      x - TILE_SIZE * 3.1, y + TILE_SIZE * 2.4,
                    ])
                    .fill(0x5c3a21)

                  // Mast
                  graphics
                    .rect(
                      x + TILE_SIZE * 0.35,
                      y - TILE_SIZE * 4.8,
                      TILE_SIZE * 0.3,
                      TILE_SIZE * 6.5,
                    )
                    .fill(0x3b2a1f)

                  // Right sail
                  graphics
                    .poly([
                      x + TILE_SIZE * 0.8, y - TILE_SIZE * 4.5,
                      x + TILE_SIZE * 4.0, y - TILE_SIZE * 3.3,
                      x + TILE_SIZE * 3.5, y + TILE_SIZE * 0.8,
                      x + TILE_SIZE * 0.8, y + TILE_SIZE * 0.8,
                    ])
                    .fill(0xf4e4bc)

                  // Left sail
                  graphics
                    .poly([
                      x + TILE_SIZE * 0.2, y - TILE_SIZE * 4.1,
                      x - TILE_SIZE * 3.2, y - TILE_SIZE * 3.0,
                      x - TILE_SIZE * 2.7, y + TILE_SIZE * 0.8,
                      x + TILE_SIZE * 0.2, y + TILE_SIZE * 0.8,
                    ])
                    .fill(0xe8d39f)
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

            <pixiGraphics
              draw={(graphics) => {
                graphics.clear()

                for (const tourist of tourists) {
                  if (tourist.insideTemple) {
                    continue
                  }

                  const touristX = tourist.x * TILE_SIZE
                  const touristY = tourist.y * TILE_SIZE

                  const centerX = touristX + TILE_SIZE
                  const baseY = touristY + TILE_SIZE * 2

                  const bodyRadius = TILE_SIZE * 0.6
                  const headRadius = TILE_SIZE * 0.4

                  const bodyCenterY = baseY - bodyRadius
                  const headCenterY =
                    bodyCenterY - bodyRadius - headRadius * 0.5

                  // Shirt color varies a bit by state so you can eyeball behavior
                  const shirtColor =
                    tourist.state === 'inside_temple' ? 0xd4af37 : 0xdd4444

                  graphics
                    .circle(centerX, bodyCenterY, bodyRadius)
                    .fill(shirtColor)

                  graphics
                    .circle(centerX, headCenterY, headRadius)
                    .fill(0xf0c8a0)
                }
              }}
            />
            <pixiGraphics
              draw={(graphics) => {
                graphics.clear()

                const drawSelectionBox = (
                  centerX: number,
                  centerY: number,
                  boxSize: number,
                ) => {
                  const left = centerX - boxSize / 2
                  const top = centerY - boxSize / 2

                  const cornerLength = boxSize * 0.3

                  // Transparent green background
                  graphics
                    .rect(
                      left,
                      top,
                      boxSize,
                      boxSize,
                    )
                    .fill({
                      color: 0x22c55e,
                      alpha: 0.18,
                    })

                  // Top-left
                  graphics
                    .moveTo(left, top + cornerLength)
                    .lineTo(left, top)
                    .lineTo(left + cornerLength, top)
                    .stroke({
                      width: 2,
                      color: 0xffffff,
                    })

                  // Top-right
                  graphics
                    .moveTo(
                      left + boxSize - cornerLength,
                      top,
                    )
                    .lineTo(
                      left + boxSize,
                      top,
                    )
                    .lineTo(
                      left + boxSize,
                      top + cornerLength,
                    )
                    .stroke({
                      width: 2,
                      color: 0xffffff,
                    })

                  // Bottom-left
                  graphics
                    .moveTo(
                      left,
                      top + boxSize - cornerLength,
                    )
                    .lineTo(
                      left,
                      top + boxSize,
                    )
                    .lineTo(
                      left + cornerLength,
                      top + boxSize,
                    )
                    .stroke({
                      width: 2,
                      color: 0xffffff,
                    })

                  // Bottom-right
                  graphics
                    .moveTo(
                      left + boxSize - cornerLength,
                      top + boxSize,
                    )
                    .lineTo(
                      left + boxSize,
                      top + boxSize,
                    )
                    .lineTo(
                      left + boxSize,
                      top + boxSize - cornerLength,
                    )
                    .stroke({
                      width: 2,
                      color: 0xffffff,
                    })
                }

                if (selectedMonkeyId !== null) {
                  const monkey = monkeys.find(
                    (monkey) =>
                      monkey.id === selectedMonkeyId,
                  )

                  if (monkey) {
                    const scale = getMonkeyScale(
                      monkey.life_stage,
                    )

                    const centerX =
                      monkey.x * TILE_SIZE + TILE_SIZE

                    const centerY =
                      monkey.y * TILE_SIZE + TILE_SIZE

                    const boxSize =
                      TILE_SIZE * 3 * scale

                    drawSelectionBox(
                      centerX,
                      centerY,
                      boxSize,
                    )
                  }
                }

                if (selectedTouristId !== null) {
                  const tourist = tourists.find(
                    (tourist) =>
                      tourist.id === selectedTouristId,
                  )

                  if (
                    tourist &&
                    !tourist.insideTemple
                  ) {
                    const centerX =
                      tourist.x * TILE_SIZE + TILE_SIZE

                    const centerY =
                      tourist.y * TILE_SIZE + TILE_SIZE

                    const boxSize = TILE_SIZE * 3

                    drawSelectionBox(
                      centerX,
                      centerY,
                      boxSize,
                    )
                  }
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
