import { useEffect, useRef, useState } from 'react'

import { type WorldMeta, type Viewport, TERRAIN_COLOR } from './types'

type ThumbnailResponse = {
  w: number
  h: number
  terrain: string
}

type MinimapProps = {
  worldMeta: WorldMeta
  viewport: Viewport | null
  apiBase: string
}

const MINIMAP_SIZE = 160 // px, fits the longer world dimension


function Minimap({ worldMeta, viewport, apiBase }: MinimapProps) {
  const { width, height } = worldMeta
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false

    fetch(`${apiBase}/world/thumbnail`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data: ThumbnailResponse) => {
        if (cancelled) return

        const canvas = document.createElement('canvas')
        canvas.width = data.w
        canvas.height = data.h
        const ctx = canvas.getContext('2d')
        if (!ctx) return

        const imageData = ctx.createImageData(data.w, data.h)
        for (let i = 0; i < data.terrain.length; i++) {
          const [r, g, b] = TERRAIN_COLOR[data.terrain[i]] ?? [0, 0, 0]
          imageData.data[i * 4] = r
          imageData.data[i * 4 + 1] = g
          imageData.data[i * 4 + 2] = b
          imageData.data[i * 4 + 3] = 255
        }
        ctx.putImageData(imageData, 0, 0)

        setThumbnailUrl(canvas.toDataURL())
      })
      .catch((err) => {
        console.error('Thumbnail fetch failed:', err)
      })

    return () => {
      cancelled = true
    }
  }, [apiBase])

  // Fit the longer world dimension into MINIMAP_SIZE, keep aspect ratio
  const aspect = width / height
  const mapWidth = aspect >= 1 ? MINIMAP_SIZE : MINIMAP_SIZE * aspect
  const mapHeight = aspect >= 1 ? MINIMAP_SIZE / aspect : MINIMAP_SIZE

  const rectStyle = viewport
    ? {
        left: `${(viewport.x / width) * 100}%`,
        top: `${(viewport.y / height) * 100}%`,
        width: `${(viewport.width / width) * 100}%`,
        height: `${(viewport.height / height) * 100}%`,
      }
    : null

  return (
    <div
      ref={containerRef}
      style={{
        position: 'absolute',
        top: 12,
        right: 12,
        width: mapWidth,
        height: mapHeight,
        border: '2px solid rgba(255, 255, 255, 0.6)',
        borderRadius: 4,
        overflow: 'hidden',
        backgroundColor: '#111',
        backgroundImage: thumbnailUrl ? `url(${thumbnailUrl})` : undefined,
        backgroundSize: '100% 100%', // stretch to fill - thumbnail already matches aspect
        imageRendering: 'pixelated', // keep it crisp like the main map, not blurry
      }}
    >
      {rectStyle && (
        <div
          style={{
            position: 'absolute',
            border: '1.5px solid #ffffff',
            boxShadow: '0 0 4px rgba(0, 0, 0, 0.8)',
            pointerEvents: 'none',
            ...rectStyle,
          }}
        />
      )}
    </div>
  )
}

export default Minimap
