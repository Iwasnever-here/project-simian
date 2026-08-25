export type WorldMeta = {
  width: number
  height: number
  chunkSize: number
  day: number
  hour: number
  isDaytime: boolean
}

export type Viewport = {
  x: number
  y: number
  width: number
  height: number
}

export const TERRAIN_COLOR: Record<string, [number, number, number]> = {
  w: [100, 149, 237],
  s: [245, 222, 179],
  g: [110, 139, 61],
  f: [74, 93, 35],
  m: [85, 93, 80],
  r: [120, 110, 100],
  n: [240, 245, 250],
}