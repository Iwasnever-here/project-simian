import { Application, extend } from '@pixi/react'
import { Container, Graphics, Sprite, Texture, FederatedPointerEvent } from 'pixi.js'
import { useCallback, useEffect, useRef, useState } from 'react'

extend({
  Container,
  Graphics,
  Sprite,
})

type WorldMeta = {
  width: number
  height: number
  chunkSize: number
}

type WorldCanvasProps = {
  worldMeta: WorldMeta
  apiBase: string
}

type ChunkResponse = {
  cx: number
  cy: number
  w: number
  h: number
  terrain: string
}

const TILE_SIZE = 8 // px per tile on screen - shrink further for even bigger worlds
const VIEWPORT_WIDTH = 800
const VIEWPORT_HEIGHT = 600
const LOAD_MARGIN_CHUNKS = 1 // preload one extra ring of chunks around the viewport

const TERRAIN_COLOR: Record<string, [number, number, number]> = {
  w: [30, 144, 255],  // water
  s: [245, 222, 179], // sand
  g: [79, 143, 58],   // grass
}

function chunkKey(cx: number, cy: number) {
  return `${cx}:${cy}`
}

function WorldCanvas({ worldMeta, apiBase }: WorldCanvasProps) {
  const { width, height, chunkSize } = worldMeta
  const chunkPixelSize = chunkSize * TILE_SIZE

  // Camera position lives in a ref so dragging doesn't trigger React re-renders.
  // The container's x/y are set imperatively on every pointer move for smoothness.
  const cameraRef = useRef({ x: 0, y: 0 })
  const containerRef = useRef<Container>(null)

  const [dragging, setDragging] = useState(false)
  const lastPointerRef = useRef({ x: 0, y: 0 })

  const texturesRef = useRef<Map<string, Texture>>(new Map())
  const loadingRef = useRef<Set<string>>(new Set())
  const [, bumpVersion] = useState(0)
  const forceRender = useCallback(() => bumpVersion((n) => n + 1), [])

  const loadChunk = useCallback(
    async (cx: number, cy: number) => {
      const key = chunkKey(cx, cy)
      if (texturesRef.current.has(key) || loadingRef.current.has(key)) return
      loadingRef.current.add(key)

      try {
        const res = await fetch(`${apiBase}/world/chunk/${cx}/${cy}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data: ChunkResponse = await res.json()

        // Bake the chunk's terrain into a small canvas, one pixel per tile,
        // then let Pixi scale it up - this avoids drawing thousands of rects.
        const canvas = document.createElement('canvas')
        canvas.width = data.w
        canvas.height = data.h
        const ctx = canvas.getContext('2d')
        if (!ctx) throw new Error('2D context unavailable')

        const imageData = ctx.createImageData(data.w, data.h)
        for (let i = 0; i < data.terrain.length; i++) {
          const [r, g, b] = TERRAIN_COLOR[data.terrain[i]] ?? [0, 0, 0]
          imageData.data[i * 4] = r
          imageData.data[i * 4 + 1] = g
          imageData.data[i * 4 + 2] = b
          imageData.data[i * 4 + 3] = 255
        }
        ctx.putImageData(imageData, 0, 0)

        const texture = Texture.from(canvas)
        texture.source.scaleMode = 'nearest' // keep tile edges crisp when scaled up
        texturesRef.current.set(key, texture)
      } catch (err) {
        console.error(`Chunk fetch failed (${cx}, ${cy}):`, err)
      } finally {
        loadingRef.current.delete(key)
        forceRender()
      }
    },
    [apiBase, forceRender],
  )

  const maxCx = Math.ceil(width / chunkSize) - 1
  const maxCy = Math.ceil(height / chunkSize) - 1

  const updateVisibleChunks = useCallback(() => {
    const { x: camX, y: camY } = cameraRef.current

    const startCx = Math.max(0, Math.floor(-camX / chunkPixelSize) - LOAD_MARGIN_CHUNKS)
    const endCx = Math.min(
      maxCx,
      Math.floor((-camX + VIEWPORT_WIDTH) / chunkPixelSize) + LOAD_MARGIN_CHUNKS,
    )
    const startCy = Math.max(0, Math.floor(-camY / chunkPixelSize) - LOAD_MARGIN_CHUNKS)
    const endCy = Math.min(
      maxCy,
      Math.floor((-camY + VIEWPORT_HEIGHT) / chunkPixelSize) + LOAD_MARGIN_CHUNKS,
    )

    for (let cy = startCy; cy <= endCy; cy++) {
      for (let cx = startCx; cx <= endCx; cx++) {
        loadChunk(cx, cy)
      }
    }
  }, [chunkPixelSize, maxCx, maxCy, loadChunk])

  // Initial load for the starting viewport
  useEffect(() => {
    updateVisibleChunks()
  }, [updateVisibleChunks])

  // Throttle chunk-visibility checks during drag so we're not scanning ranges every pixel
  const throttleRef = useRef<number | null>(null)
  const scheduleViewUpdate = useCallback(() => {
    if (throttleRef.current !== null) return
    throttleRef.current = window.setTimeout(() => {
      throttleRef.current = null
      updateVisibleChunks()
    }, 150)
  }, [updateVisibleChunks])

  const loadedChunks = Array.from(texturesRef.current.entries())

  return (
    <Application
      width={VIEWPORT_WIDTH}
      height={VIEWPORT_HEIGHT}
      backgroundColor={0x1E90FF}
    >
      <pixiContainer
        ref={containerRef}
        x={cameraRef.current.x}
        y={cameraRef.current.y}
      >
        {loadedChunks.map(([key, texture]) => {
          const [cx, cy] = key.split(':').map(Number)
          return (
            <pixiSprite
              key={key}
              texture={texture}
              x={cx * chunkPixelSize}
              y={cy * chunkPixelSize}
              width={chunkPixelSize}
              height={chunkPixelSize}
            />
          )
        })}
      </pixiContainer>

      <pixiGraphics
        eventMode="static"
        cursor={dragging ? 'grabbing' : 'grab'}
        draw={(graphics) => {
          graphics.clear()

          graphics
            .rect(0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
            .fill({
              color: 0x000000,
              alpha: 0,
            })
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

          // Mutate camera + container directly - no setState, no re-render, stays smooth
          cameraRef.current.x += dx
          cameraRef.current.y += dy
          if (containerRef.current) {
            containerRef.current.x = cameraRef.current.x
            containerRef.current.y = cameraRef.current.y
          }

          lastPointerRef.current = { x: currentX, y: currentY }
          scheduleViewUpdate()
        }}
        onPointerUp={() => {
          setDragging(false)
          updateVisibleChunks()
        }}
        onPointerUpOutside={() => {
          setDragging(false)
          updateVisibleChunks()
        }}
      />
    </Application>
  )
}

export default WorldCanvas
