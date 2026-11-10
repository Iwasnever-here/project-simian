import { useState } from 'react'

export type PopulationSample = {
  tick: number
  day: number
  alive: number
  deaths: number
  total: number
}

const metrics = [
  { key: 'alive', label: 'Alive', color: 'var(--simian-green)' },
  { key: 'deaths', label: 'Deaths', color: 'var(--simian-red)' },
  { key: 'total', label: 'Born', color: 'var(--simian-blue)' },
] as const

type Props = {
  alive: number | null
  deaths: number | null
  total: number | null
  history: PopulationSample[]
}

function StatCard({
  label,
  value,
}: {
  label: string
  value: number | null
}) {
  return (
    <div className="stat-card">
      <strong>{value ?? '...'}</strong>
      <span>{label}</span>
    </div>
  )
}

function PopulationChart({ history }: { history: PopulationSample[] }) {
  const [metric, setMetric] = useState<(typeof metrics)[number]>(metrics[0])
  const first = history[0]
  const last = history.at(-1)
  const duration = first && last ? last.tick - first.tick : 0
  let min = first?.[metric.key] ?? 0
  let max = min
  for (const sample of history) {
    min = Math.min(min, sample[metric.key])
    max = Math.max(max, sample[metric.key])
  }
  max = Math.max(min + 1, max)
  const points = duration > 0
    ? history.map((sample) => {
        const x = 4 + (sample.tick - first.tick) / duration * 192
        const y = 69 - (sample[metric.key] - min) / (max - min) * 62
        return `${x},${y}`
      }).join(' ')
    : ''

  return (
    <section className="panel-section population-chart">
      <div className="panel-section__title">Population since start</div>
      <div className="population-chart__switch" role="group" aria-label="Population metric">
        {metrics.map((option) => (
          <button
            type="button"
            key={option.key}
            aria-pressed={option.key === metric.key}
            onClick={() => setMetric(option)}
          >
            {option.label}
          </button>
        ))}
      </div>
      {points ? (
        <>
          <div className="population-chart__plot">
            <svg viewBox="0 0 200 76" preserveAspectRatio="none" role="img"
              aria-label={`${metric.label} over time, latest count ${last?.[metric.key]}`}
            >
              <path d="M4 7H196 M4 38H196 M4 69H196" className="population-chart__grid" />
              <polyline points={points} fill="none" stroke={metric.color}
                strokeWidth="2" vectorEffect="non-scaling-stroke"
                strokeLinejoin="round" strokeLinecap="round"
              />
            </svg>
            <div className="population-chart__scale" aria-hidden="true">
              <span>{max}</span>
              <span>{min}</span>
            </div>
          </div>
          <div className="population-chart__time">
            <span>Day {first?.day}</span>
            <span>Day {last?.day}</span>
          </div>
        </>
      ) : <p className="panel-copy">Waiting for population history…</p>}
    </section>
  )
}

function PopulationPanel({
  alive,
  deaths,
  total,
  history,
}: Props) {
  const mortality =
    total !== null &&
    deaths !== null &&
    total > 0
      ? Math.round((deaths / total) * 100)
      : 0

  const survival = 100 - mortality

  return (
    <aside className="panel population-panel">
      <div className="panel__header">
        <div>
          <div className="panel__eyebrow">
            WORLD
          </div>

          <h2>Population</h2>
        </div>

        <span className="panel__header-icon">
          ◉
        </span>
      </div>

      <div className="population-grid">
        <StatCard
          label="Alive"
          value={alive}
        />

        <StatCard
          label="Deaths"
          value={deaths}
        />

        <StatCard
          label="Total Born"
          value={total}
        />

        <div className="stat-card">
          <strong>{mortality}%</strong>
          <span>Mortality</span>
        </div>
      </div>

      <section className="panel-section">
        <div className="panel-section__title">
          Population Health
        </div>

        <div className="mini-stat">
          <span>Survival</span>
          <strong>{survival}%</strong>
        </div>

        <div className="progress-track progress-track--wide">
          <div
            className="progress-fill progress-fill--health"
            style={{
              width: `${survival}%`,
            }}
          />
        </div>
      </section>

      <PopulationChart history={history} />
    </aside>
  )
}

export default PopulationPanel
