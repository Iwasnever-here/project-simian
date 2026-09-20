import { Application, extend, useApplication } from '@pixi/react'
import {
  Container,
  Graphics,
  Sprite,
  Texture,
  FederatedPointerEvent,
} from 'pixi.js'
import {
  memo,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'

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
  cx: number
  cy: number
  texture: Texture
  trees: TreeData[]
  width: number
  height: number
}

type SelectionTarget = {
  x: number
  y: number
  size: number
}

const TILE_SIZE = 8

const VIEWPORT_WIDTH = 900
const VIEWPORT_HEIGHT = 600

const LOAD_MARGIN_CHUNKS = 1
// Chunks further than this (beyond the load margin) are freed.
const EVICT_EXTRA_CHUNKS = 2

const MONKEY_POLL_INTERVAL = 1000
const TOURIST_POLL_INTERVAL = 1000

const MIN_ZOOM = 0.5
const MAX_ZOOM = 4
const ZOOM_SPEED = 0.0015

// Pixi renders every frame by default (60fps+, more on high-refresh screens).
// The world only really changes once a second, so 30 is plenty.
const MAX_FPS = 30

const NO_TARGETS: SelectionTarget[] = []

/* -------------------------------------------------------------------------- */
/* Pure helpers (defined outside the component so they are never recreated)   */
/* -------------------------------------------------------------------------- */

function getMonkeyScale(lifeStage: string) {
  if (lifeStage === 'infant') {
    return 0.5
  }

  if (lifeStage === 'juvenile') {
    return 0.75
  }

  return 1
}

function getNightAlpha(hour: number) {
  // Full daylight: 08:00 - 17:00
  if (hour >= 8 && hour < 17) {
    return 0
  }

  // Sunset: 17:00 - 20:00
  if (hour >= 17 && hour < 20) {
    return ((hour - 17) / 3) * 0.5
  }

  // Full night: 20:00 - 05:00
  if (hour >= 20 || hour < 5) {
    return 0.5
  }

  // Sunrise: 05:00 - 08:00
  return 0.5 * (1 - (hour - 5) / 3)
}

function chunkKey(cx: number, cy: number) {
  return `${cx}:${cy}`
}

function drawTrees(graphics: Graphics, trees: TreeData[]) {
  graphics.clear()

  // Batch all trunks into one fill and all crowns into another, rather than
  // two fill() calls per tree.
  for (const tree of trees) {
    graphics.rect(tree.x * TILE_SIZE + 3, tree.y * TILE_SIZE + 4, 2, 4)
  }
  graphics.fill(0x6b4423)

  for (const tree of trees) {
    graphics.rect(tree.x * TILE_SIZE + 1, tree.y * TILE_SIZE + 1, 6, 5)
  }
  graphics.fill(0x123d1f)
}

function drawTemple(graphics: Graphics, temple: TempleData) {
  graphics.clear()

  const x = temple.x * TILE_SIZE
  const y = temple.y * TILE_SIZE

  const w = temple.width * TILE_SIZE
  const h = temple.height * TILE_SIZE

  const wallThickness = TILE_SIZE * 1.5
  const towerRadius = TILE_SIZE * 1.8
  const entranceWidth = TILE_SIZE * 2

  // Outer platform
  graphics
    .rect(x - TILE_SIZE, y - TILE_SIZE, w + TILE_SIZE * 2, h + TILE_SIZE * 2)
    .fill(0x9f9270)

  // Main temple floor
  graphics.rect(x, y, w, h).fill(0xc2b280)

  // Inner courtyard
  graphics
    .rect(
      x + wallThickness,
      y + wallThickness,
      w - wallThickness * 2,
      h - wallThickness * 2,
    )
    .fill(0xd6c69c)

  // Walls (top, left, right, bottom-left, bottom-right) in a single fill
  graphics
    .rect(x, y, w, wallThickness)
    .rect(x, y, wallThickness, h)
    .rect(x + w - wallThickness, y, wallThickness, h)
    .rect(
      x,
      y + h - wallThickness,
      w / 2 - entranceWidth / 2,
      wallThickness,
    )
    .rect(
      x + w / 2 + entranceWidth / 2,
      y + h - wallThickness,
      w / 2 - entranceWidth / 2,
      wallThickness,
    )
    .fill(0x6b6045)

  // Corner towers
  graphics
    .circle(x, y, towerRadius)
    .circle(x + w, y, towerRadius)
    .circle(x, y + h, towerRadius)
    .circle(x + w, y + h, towerRadius)
    .fill(0x786b4d)

  // Entrance
  graphics
    .rect(
      temple.entrance.x * TILE_SIZE - TILE_SIZE / 2,
      temple.entrance.y * TILE_SIZE,
      entranceWidth,
      TILE_SIZE,
    )
    .fill(0x3b2a1f)

  // Central shrine
  graphics.circle(x + w / 2, y + h / 2, TILE_SIZE * 0.8).fill(0x8f7d52)
}

function drawBoatLanding(graphics: Graphics, landing: BoatLandingData) {
  graphics.clear()

  const x = landing.x * TILE_SIZE
  const y = landing.y * TILE_SIZE
  const T = TILE_SIZE

  // Dock
  graphics
    .rect(x - T * 2, y + T * 4, T * 6, T * 0.8)
    .fill(0x8b6f47)

  // Large hull
  graphics
    .poly([
      x - T * 3.5, y + T * 1.5,
      x + T * 4.5, y + T * 1.5,

      x + T * 3.8, y + T * 2.8,
      x + T * 3.0, y + T * 3.6,
      x + T * 2.0, y + T * 4.1,
      x + T * 0.8, y + T * 4.4,

      x - T * 0.5, y + T * 4.3,
      x - T * 1.6, y + T * 3.9,
      x - T * 2.5, y + T * 3.2,
      x - T * 3.1, y + T * 2.4,
    ])
    .fill(0x5c3a21)

  // Mast
  graphics
    .rect(x + T * 0.35, y - T * 4.8, T * 0.3, T * 6.5)
    .fill(0x3b2a1f)

  // Right sail
  graphics
    .poly([
      x + T * 0.8, y - T * 4.5,
      x + T * 4.0, y - T * 3.3,
      x + T * 3.5, y + T * 0.8,
      x + T * 0.8, y + T * 0.8,
    ])
    .fill(0xf4e4bc)

  // Left sail
  graphics
    .poly([
      x + T * 0.2, y - T * 4.1,
      x - T * 3.2, y - T * 3.0,
      x - T * 2.7, y + T * 0.8,
      x + T * 0.2, y + T * 0.8,
    ])
    .fill(0xe8d39f)
}

function drawMonkeys(graphics: Graphics, monkeys: MonkeyData[]) {
  graphics.clear()

  for (const monkey of monkeys) {
    const scale = getMonkeyScale(monkey.life_stage)

    const centerX = monkey.x * TILE_SIZE + TILE_SIZE
    const baseY = monkey.y * TILE_SIZE + TILE_SIZE * 2

    const bodyRadius = TILE_SIZE * 0.7 * scale
    const headRadius = TILE_SIZE * 0.5 * scale
    const earRadius = TILE_SIZE * 0.2 * scale

    const bodyCenterY = baseY - bodyRadius
    const headCenterY = bodyCenterY - bodyRadius - headRadius * 0.5

    graphics.circle(centerX, bodyCenterY, bodyRadius).fill(0x6b4423)

    graphics
      .circle(centerX, headCenterY, headRadius)
      .circle(centerX - headRadius, headCenterY, earRadius)
      .circle(centerX + headRadius, headCenterY, earRadius)
      .fill(0x7a5230)
  }
}

function drawTourists(graphics: Graphics, tourists: TouristData[]) {
  graphics.clear()

  for (const tourist of tourists) {
    if (tourist.insideTemple) {
      continue
    }

    const centerX = tourist.x * TILE_SIZE + TILE_SIZE
    const baseY = tourist.y * TILE_SIZE + TILE_SIZE * 2

    const bodyRadius = TILE_SIZE * 0.6
    const headRadius = TILE_SIZE * 0.4

    const bodyCenterY = baseY - bodyRadius
    const headCenterY = bodyCenterY - bodyRadius - headRadius * 0.5

    const shirtColor = tourist.state === 'inside_temple' ? 0xd4af37 : 0xdd4444

    graphics.circle(centerX, bodyCenterY, bodyRadius).fill(shirtColor)
    graphics.circle(centerX, headCenterY, headRadius).fill(0xf0c8a0)
  }
}

function drawSelectionBox(
  graphics: Graphics,
  centerX: number,
  centerY: number,
  boxSize: number,
) {
  const left = centerX - boxSize / 2
  const top = centerY - boxSize / 2
  const right = left + boxSize
  const bottom = top + boxSize
  const c = boxSize * 0.3

  // Transparent green background
  graphics
    .rect(left, top, boxSize, boxSize)
    .fill({ color: 0x22c55e, alpha: 0.18 })

  // All four corner brackets as one path, one stroke
  graphics
    .moveTo(left, top + c).lineTo(left, top).lineTo(left + c, top)
    .moveTo(right - c, top).lineTo(right, top).lineTo(right, top + c)
    .moveTo(left, bottom - c).lineTo(left, bottom).lineTo(left + c, bottom)
    .moveTo(right - c, bottom).lineTo(right, bottom).lineTo(right, bottom - c)
    .stroke({ width: 2, color: 0xffffff })
}

// Stable draw callbacks for things that never change
function drawNightOverlay(graphics: Graphics) {
  graphics.clear()
  graphics
    .rect(0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
    .fill({ color: 0x08111f, alpha: 1 })
}

function drawHitArea(graphics: Graphics) {
  graphics.clear()
  graphics
    .rect(0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
    .fill({ color: 0x000000, alpha: 0 })
}

/* -------------------------------------------------------------------------- */
/* Data hooks                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * Polls a JSON endpoint.
 *  - chained setTimeout, so requests never overlap if the server is slow
 *  - pauses while the tab is hidden
 *  - aborts the in-flight request on unmount
 *  - skips JSON.parse + setState entirely when the body hasn't changed
 */
function usePolling<T>(
  url: string,
  intervalMs: number,
  onData: (data: T) => void,
) {
  const onDataRef = useRef(onData)
  onDataRef.current = onData

  useEffect(() => {
    let cancelled = false
    let timer: number | undefined
    let controller: AbortController | null = null
    let lastText: string | null = null

    const schedule = () => {
      if (!cancelled) {
        timer = window.setTimeout(tick, intervalMs)
      }
    }

    const tick = async () => {
      if (document.hidden) {
        schedule()
        return
      }

      controller = new AbortController()

      try {
        const response = await fetch(url, { signal: controller.signal })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const text = await response.text()

        if (!cancelled && text !== lastText) {
          lastText = text
          onDataRef.current(JSON.parse(text) as T)
        }
      } catch (error) {
        if (!cancelled) {
          console.error(`Fetch failed (${url}):`, error)
        }
      }

      schedule()
    }

    tick()

    return () => {
      cancelled = true
      window.clearTimeout(timer)
      controller?.abort()
    }
  }, [url, intervalMs])
}

function useFetchOnce<T>(url: string, onData: (data: T) => void) {
  const onDataRef = useRef(onData)
  onDataRef.current = onData

  useEffect(() => {
    const controller = new AbortController()

    fetch(url, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        return response.json() as Promise<T>
      })
      .then((data) => onDataRef.current(data))
      .catch((error) => {
        if (!controller.signal.aborted) {
          console.error(`Fetch failed (${url}):`, error)
        }
      })

    return () => controller.abort()
  }, [url])
}

/* -------------------------------------------------------------------------- */
/* Memoised scene pieces                                                      */
/* -------------------------------------------------------------------------- */

/** Caps the Pixi ticker. Must be rendered inside <Application>. */
function FrameLimiter({ fps }: { fps: number }) {
  const { app, isInitialised } = useApplication()

  useEffect(() => {
    if (isInitialised && app.ticker) {
      app.ticker.maxFPS = fps
    }
  }, [app, isInitialised, fps])

  return null
}

const ChunkView = memo(function ChunkView({
  chunk,
  x,
  y,
}: {
  chunk: LoadedChunk
  x: number
  y: number
}) {
  const draw = useCallback(
    (graphics: Graphics) => drawTrees(graphics, chunk.trees),
    [chunk.trees],
  )

  return (
    <pixiContainer x={x} y={y}>
      <pixiSprite
        texture={chunk.texture}
        x={0}
        y={0}
        width={chunk.width * TILE_SIZE}
        height={chunk.height * TILE_SIZE}
      />
      <pixiGraphics draw={draw} />
    </pixiContainer>
  )
})

const TempleView = memo(function TempleView({ temple }: { temple: TempleData }) {
  const draw = useCallback(
    (graphics: Graphics) => drawTemple(graphics, temple),
    [temple],
  )
  return <pixiGraphics draw={draw} />
})

const BoatLandingView = memo(function BoatLandingView({
  landing,
}: {
  landing: BoatLandingData
}) {
  const draw = useCallback(
    (graphics: Graphics) => drawBoatLanding(graphics, landing),
    [landing],
  )
  return <pixiGraphics draw={draw} />
})

/* -------------------------------------------------------------------------- */
/* Main component                                                             */
/* -------------------------------------------------------------------------- */

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
  const zoomLabelRef = useRef<HTMLDivElement | null>(null)
  const lastPointerRef = useRef({ x: 0, y: 0 })
  const pointerDownRef = useRef({ x: 0, y: 0 })
  const chunksRef = useRef<Map<string, LoadedChunk>>(new Map())
  const loadingRef = useRef<Set<string>>(new Set())
  const throttleRef = useRef<number | null>(null)

  // Keep the latest callback without making it a dependency of everything
  // below (an unstable prop would otherwise re-create the wheel listener,
  // the throttle and the chunk-loading effect on every parent render).
  const onViewportChangeRef = useRef(onViewportChange)
  onViewportChangeRef.current = onViewportChange

  const [dragging, setDragging] = useState(false)
  const [monkeys, setMonkeys] = useState<MonkeyData[]>([])
  const [temple, setTemple] = useState<TempleData | null>(null)
  const [tourists, setTourists] = useState<TouristData[]>([])
  const [boatLanding, setBoatLanding] = useState<BoatLandingData | null>(null)

  const [, bumpVersion] = useState(0)
  const nightAlpha = getNightAlpha(hour)

  const forceRender = useCallback(() => {
    bumpVersion((version) => version + 1)
  }, [])

  const maxCx = Math.ceil(width / chunkSize) - 1
  const maxCy = Math.ceil(height / chunkSize) - 1

  /* ------------------------------ data loading ----------------------------- */

  usePolling<MonkeyData[]>(`${apiBase}/monkeys`, MONKEY_POLL_INTERVAL, setMonkeys)
  usePolling<TouristData[]>(
    `${apiBase}/tourists`,
    TOURIST_POLL_INTERVAL,
    setTourists,
  )
  useFetchOnce<TempleData>(`${apiBase}/temple`, setTemple)
  useFetchOnce<BoatLandingData>(`${apiBase}/boat-landing`, setBoatLanding)

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
          cx,
          cy,
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

  const updateVisibleChunks = useCallback(() => {
    const { x: cameraX, y: cameraY, zoom: cameraZoom } = cameraRef.current

    // Convert the visible screen area back into world pixel coordinates.
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

    // Free chunks that are well outside the view so the scene graph and
    // texture memory don't grow forever as the user pans around.
    const stale: Texture[] = []

    for (const [key, chunk] of chunksRef.current) {
      if (
        chunk.cx < startCx - EVICT_EXTRA_CHUNKS ||
        chunk.cx > endCx + EVICT_EXTRA_CHUNKS ||
        chunk.cy < startCy - EVICT_EXTRA_CHUNKS ||
        chunk.cy > endCy + EVICT_EXTRA_CHUNKS
      ) {
        chunksRef.current.delete(key)
        stale.push(chunk.texture)
      }
    }

    if (stale.length > 0) {
      forceRender()

      // Destroy a little later so the sprite is definitely gone from the
      // scene before its texture is.
      window.setTimeout(() => {
        for (const texture of stale) {
          texture.destroy(true)
        }
      }, 1000)
    }

    // This is also what keeps the minimap viewport correct.
    onViewportChangeRef.current?.({
      x: worldLeft / TILE_SIZE,
      y: worldTop / TILE_SIZE,
      width: VIEWPORT_WIDTH / (TILE_SIZE * cameraZoom),
      height: VIEWPORT_HEIGHT / (TILE_SIZE * cameraZoom),
    })
  }, [chunkPixelSize, maxCx, maxCy, loadChunk, forceRender])

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
    const chunks = chunksRef.current

    return () => {
      if (throttleRef.current !== null) {
        window.clearTimeout(throttleRef.current)
      }

      for (const chunk of chunks.values()) {
        chunk.texture.destroy(true)
      }

      chunks.clear()
    }
  }, [])

  /* ------------------------------ interaction ------------------------------ */

  const handleWorldClick = useCallback(
    (event: FederatedPointerEvent) => {
      const camera = cameraRef.current

      const worldPixelX = (event.global.x - camera.x) / camera.zoom
      const worldPixelY = (event.global.y - camera.y) / camera.zoom

      // Compare squared distances; no need for sqrt in a hit test.
      let closestMonkey: MonkeyData | null = null
      let closestMonkeyDistSq = Infinity

      for (const monkey of monkeys) {
        const hitRadius = TILE_SIZE * 1.2 * getMonkeyScale(monkey.life_stage)

        const dx = worldPixelX - (monkey.x * TILE_SIZE + TILE_SIZE)
        const dy = worldPixelY - (monkey.y * TILE_SIZE + TILE_SIZE)
        const distSq = dx * dx + dy * dy

        if (distSq <= hitRadius * hitRadius && distSq < closestMonkeyDistSq) {
          closestMonkey = monkey
          closestMonkeyDistSq = distSq
        }
      }

      let closestTourist: TouristData | null = null
      let closestTouristDistSq = Infinity
      const touristHitRadius = TILE_SIZE * 1.2

      for (const tourist of tourists) {
        if (tourist.insideTemple) {
          continue
        }

        const dx = worldPixelX - (tourist.x * TILE_SIZE + TILE_SIZE)
        const dy = worldPixelY - (tourist.y * TILE_SIZE + TILE_SIZE)
        const distSq = dx * dx + dy * dy

        if (
          distSq <= touristHitRadius * touristHitRadius &&
          distSq < closestTouristDistSq
        ) {
          closestTourist = tourist
          closestTouristDistSq = distSq
        }
      }

      if (
        closestMonkey &&
        (!closestTourist || closestMonkeyDistSq <= closestTouristDistSq)
      ) {
        onMonkeySelect?.(closestMonkey.id)
        onTouristSelect?.(null)
        return
      }

      if (closestTourist) {
        onTouristSelect?.(closestTourist.id)
        onMonkeySelect?.(null)
        return
      }

      onMonkeySelect?.(null)
      onTouristSelect?.(null)
    },
    [monkeys, tourists, onMonkeySelect, onTouristSelect],
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

      // World position underneath the cursor before zooming...
      const worldX = (mouseX - camera.x) / oldZoom
      const worldY = (mouseY - camera.y) / oldZoom

      // ...and move the camera so it stays underneath the cursor.
      camera.x = mouseX - worldX * nextZoom
      camera.y = mouseY - worldY * nextZoom
      camera.zoom = nextZoom

      if (containerRef.current) {
        containerRef.current.x = camera.x
        containerRef.current.y = camera.y
        containerRef.current.scale.set(nextZoom)
      }

      // Zoom label is written straight to the DOM. Using state here meant a
      // full React re-render of the world on every wheel tick.
      if (zoomLabelRef.current) {
        zoomLabelRef.current.textContent = `Zoom: ${Math.round(nextZoom * 100)}%`
      }

      scheduleViewUpdate()
    }

    element.addEventListener('wheel', handleWheel, { passive: false })

    return () => {
      element.removeEventListener('wheel', handleWheel)
    }
  }, [scheduleViewUpdate])

  /* ------------------------------ derived draws ---------------------------- */

  const drawMonkeyLayer = useCallback(
    (graphics: Graphics) => drawMonkeys(graphics, monkeys),
    [monkeys],
  )

  const drawTouristLayer = useCallback(
    (graphics: Graphics) => drawTourists(graphics, tourists),
    [tourists],
  )

  const selectionTargets = useMemo(() => {
    if (selectedMonkeyId === null && selectedTouristId === null) {
      return NO_TARGETS
    }

    const targets: SelectionTarget[] = []

    if (selectedMonkeyId !== null) {
      const monkey = monkeys.find((m) => m.id === selectedMonkeyId)

      if (monkey) {
        targets.push({
          x: monkey.x * TILE_SIZE + TILE_SIZE,
          y: monkey.y * TILE_SIZE + TILE_SIZE,
          size: TILE_SIZE * 3 * getMonkeyScale(monkey.life_stage),
        })
      }
    }

    if (selectedTouristId !== null) {
      const tourist = tourists.find((t) => t.id === selectedTouristId)

      if (tourist && !tourist.insideTemple) {
        targets.push({
          x: tourist.x * TILE_SIZE + TILE_SIZE,
          y: tourist.y * TILE_SIZE + TILE_SIZE,
          size: TILE_SIZE * 3,
        })
      }
    }

    return targets.length > 0 ? targets : NO_TARGETS
  }, [monkeys, tourists, selectedMonkeyId, selectedTouristId])

  const drawSelectionLayer = useCallback(
    (graphics: Graphics) => {
      graphics.clear()

      for (const target of selectionTargets) {
        drawSelectionBox(graphics, target.x, target.y, target.size)
      }
    },
    [selectionTargets],
  )

  /* -------------------------------- render --------------------------------- */

  const loadedChunks = Array.from(chunksRef.current.values())

  return (
    <div>
      <div
        ref={wrapperRef}
        style={{
          position: 'relative',
          width: VIEWPORT_WIDTH,
          height: VIEWPORT_HEIGHT,
        }}
      >
        <Application
          width={VIEWPORT_WIDTH}
          height={VIEWPORT_HEIGHT}
          backgroundColor={0x6495ed}
        >
          <FrameLimiter fps={MAX_FPS} />

          <pixiContainer ref={containerRef}>
            {loadedChunks.map((chunk) => (
              <ChunkView
                key={chunkKey(chunk.cx, chunk.cy)}
                chunk={chunk}
                x={chunk.cx * chunkPixelSize}
                y={chunk.cy * chunkPixelSize}
              />
            ))}

            {temple && <TempleView temple={temple} />}
            {boatLanding && <BoatLandingView landing={boatLanding} />}

            <pixiGraphics draw={drawMonkeyLayer} />
            <pixiGraphics draw={drawTouristLayer} />
            <pixiGraphics draw={drawSelectionLayer} />
          </pixiContainer>

          {/* Drawn once; the day/night cycle only changes alpha. */}
          <pixiGraphics
            draw={drawNightOverlay}
            alpha={nightAlpha}
            visible={nightAlpha > 0}
          />

          <pixiGraphics
            eventMode="static"
            cursor={dragging ? 'grabbing' : 'grab'}
            draw={drawHitArea}
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

              cameraRef.current.x += currentX - lastPointerRef.current.x
              cameraRef.current.y += currentY - lastPointerRef.current.y

              if (containerRef.current) {
                containerRef.current.x = cameraRef.current.x
                containerRef.current.y = cameraRef.current.y
              }

              lastPointerRef.current = { x: currentX, y: currentY }

              scheduleViewUpdate()
            }}
            onPointerUp={(event: FederatedPointerEvent) => {
              setDragging(false)

              const movementX = Math.abs(
                event.global.x - pointerDownRef.current.x,
              )
              const movementY = Math.abs(
                event.global.y - pointerDownRef.current.y,
              )

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

      <div ref={zoomLabelRef} style={{ marginTop: 8, fontSize: 14 }}>
        Zoom: 100%
      </div>
    </div>
  )
}

export default memo(WorldCanvas)
