import { useEffect, useState } from 'react'

export default function useSelectedEntity<T>(
  url: string | null,
  clearSelection: (id: null) => void,
): T | null {
  const [result, setResult] = useState<{ url: string; data: T } | null>(null)

  useEffect(() => {
    setResult(null)
    if (url === null) return

    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined

    const poll = async () => {
      try {
        const response = await fetch(url, { signal: controller.signal })
        if (controller.signal.aborted) return
        if (response.status === 404) {
          setResult(null)
          clearSelection(null)
          return
        }
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const data: T = await response.json()
        if (!controller.signal.aborted) setResult({ url, data })
      } catch (error) {
        if (!controller.signal.aborted) console.error('Selected entity fetch failed:', error)
      }
      if (!controller.signal.aborted) timer = setTimeout(poll, 1000)
    }

    void poll()
    return () => {
      controller.abort()
      clearTimeout(timer)
    }
  }, [url, clearSelection])

  return result && result.url === url ? result.data : null
}
