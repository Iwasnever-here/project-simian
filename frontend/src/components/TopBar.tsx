import { useEffect, useMemo, useState } from 'react'
import type { SimulationEvent } from '../App'

type Props = {
  day: number
  formattedTime: string
  isDaytime: boolean
  paused: boolean | null
  simulationSpeed: number | null
  events?: SimulationEvent[]
  onPauseToggle: () => void
  onSpeedChange: (speed: number) => void
}

function TopBar({
  day,
  formattedTime,
  isDaytime,
  paused,
  simulationSpeed,
  events = [],
  onPauseToggle,
  onSpeedChange,
}: Props) {
  const [tickerIndex, setTickerIndex] = useState(0)

  const tickerEvents = useMemo(
    () => (Array.isArray(events) ? events.slice(0, 8) : []),
    [events],
  )

  useEffect(() => {
    if (tickerEvents.length <= 1) {
      return
    }

    const interval = window.setInterval(() => {
      setTickerIndex(
        (current) => (current + 1) % tickerEvents.length,
      )
    }, 4500)

    return () => {
      window.clearInterval(interval)
    }
  }, [tickerEvents.length])

  useEffect(() => {
    if (tickerEvents.length === 0) {
      setTickerIndex(0)
      return
    }

    if (tickerIndex >= tickerEvents.length) {
      setTickerIndex(0)
    }
  }, [tickerEvents.length, tickerIndex])

  const currentEvent = tickerEvents[tickerIndex]

  return (
    <header className="simian-topbar">
      <div className="simian-brand">
        <div className="simian-brand__icon">🐒</div>

        <div>
          <div className="simian-brand__title">
            Project Simian
          </div>

          <div className="simian-brand__subtitle">
            Agent-Based Primate Simulation
          </div>
        </div>
      </div>

      <div className="news-ticker">
        <div className="news-ticker__tag">
          NEWS
        </div>

        <div className="news-ticker__content">
          {currentEvent ? (
            <>
              <span
                className={`event-dot event-dot--${currentEvent.type}`}
              />

              <strong>
                Day {currentEvent.day}
              </strong>

              <span className="news-ticker__message">
                {currentEvent.message}
              </span>
            </>
          ) : (
            <span className="news-ticker__message">
              The island is quiet. For now.
            </span>
          )}
        </div>
      </div>

      <div className="simian-clock">
        <span className="simian-clock__day">
          Day {day}
        </span>

        <strong>
          {formattedTime}
        </strong>

        <span className="simian-clock__phase">
          {isDaytime ? '☀ Day' : '☾ Night'}
        </span>
      </div>

      <div className="simian-controls">
        <button
          type="button"
          className="simian-button simian-button--primary"
          onClick={onPauseToggle}
          disabled={paused === null}
        >
          {paused === null
            ? '...'
            : paused
              ? '▶'
              : 'Ⅱ'}
        </button>

        <div className="speed-control">
          {[0.5, 1, 2, 4].map((speed) => (
            <button
              type="button"
              key={speed}
              onClick={() => onSpeedChange(speed)}
              className={
                simulationSpeed === speed
                  ? 'speed-control__button speed-control__button--active'
                  : 'speed-control__button'
              }
              disabled={simulationSpeed === null}
            >
              {speed}×
            </button>
          ))}
        </div>
      </div>
    </header>
  )
}

export default TopBar