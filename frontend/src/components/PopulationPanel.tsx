type Props = {
  alive: number | null
  deaths: number | null
  total: number | null
  spawning: boolean
  onSpawnMonkey: () => void
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

function PopulationPanel({
  alive,
  deaths,
  total,
  spawning,
  onSpawnMonkey,
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

      <section className="panel-section panel-section--grow">
        <div className="panel-section__title">
          World Notes
        </div>

        <p className="panel-copy">
          Population data updates live while the simulation
          runs. Stage and generation breakdowns can be added
          here once those values are exposed by the backend.
        </p>
      </section>

      <button
        type="button"
        className="simian-button simian-button--secondary simian-button--wide"
        onClick={onSpawnMonkey}
        disabled={spawning}
      >
        {spawning
          ? 'Spawning...'
          : '+ Spawn Monkey'}
      </button>
    </aside>
  )
}

export default PopulationPanel