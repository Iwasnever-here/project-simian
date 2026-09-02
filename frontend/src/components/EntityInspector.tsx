import type { Monkey, Tourist } from '../App'

type Props = {
  monkey: Monkey | null
  tourist: Tourist | null
  onCloseMonkey: () => void
  onCloseTourist: () => void
}

function clampPercent(value: number) {
  const percent =
    value <= 1 ? value * 100 : value

  return Math.max(
    0,
    Math.min(100, percent),
  )
}

function Meter({
  label,
  value,
  type = 'default',
}: {
  label: string
  value: number
  type?: string
}) {
  const percentage =
    clampPercent(value)

  return (
    <div className="meter-row">
      <div className="meter-row__label">
        <span>{label}</span>
        <strong>
          {Math.round(percentage)}%
        </strong>
      </div>

      <div className="progress-track">
        <div
          className={
            `progress-fill progress-fill--${type}`
          }
          style={{
            width: `${percentage}%`,
          }}
        />
      </div>
    </div>
  )
}

function formatState(state: string) {
  return state
    .replace(/_/g, ' ')
    .toLowerCase()
}

function EntityInspector({
  monkey,
  tourist,
  onCloseMonkey,
  onCloseTourist,
}: Props) {
  if (monkey) {
    return (
      <aside className="panel inspector-panel">
        <div className="panel__header">
          <div>
            <div className="panel__eyebrow">
              MONKEY #{String(monkey.id).padStart(3, '0')}
            </div>

            <h2>
              {monkey.name}
            </h2>
          </div>

          <button
            type="button"
            className="icon-button"
            onClick={onCloseMonkey}
          >
            ×
          </button>
        </div>

        <div className="entity-summary">
          <div className="entity-avatar">
            🐒
          </div>

          <div>
            <div className="entity-meta">
              {monkey.gender} · {monkey.life_stage}
            </div>

            <strong>
              Age {monkey.age}
            </strong>

            <div
              className={
                monkey.alive
                  ? 'status status--dead'
                  : 'status status--alive'
              }
            >
              <span />

              {monkey.alive
                ? 'Dead'
                : 'Alive'}
            </div>
          </div>
        </div>

        <section className="panel-section">
          <div className="panel-section__title">
            Condition
          </div>

          <Meter
            label="Health"
            value={monkey.health}
            type="health"
          />

          <Meter
            label="Energy"
            value={monkey.energy}
            type="energy"
          />

          <Meter
            label="Hunger"
            value={monkey.hunger}
            type="hunger"
          />
        </section>

        <section className="panel-section">
          <div className="panel-section__title">
            Behaviour
          </div>

          <div className="detail-row">
            <span>State</span>

            <strong className="state-pill">
              {formatState(monkey.state)}
            </strong>
          </div>

          <div className="detail-row">
            <span>Target</span>

            <strong>
              {monkey.target_monkey_id !== null
                ? `Monkey #${monkey.target_monkey_id}`
                : 'None'}
            </strong>
          </div>

          <div className="detail-row">
            <span>Position</span>

            <strong>
              {monkey.x}, {monkey.y}
            </strong>
          </div>
        </section>

        <section className="panel-section">
          <div className="panel-section__title">
            Traits
          </div>

          <Meter
            label="Boldness"
            value={monkey.traits.boldness}
          />

          <Meter
            label="Curiosity"
            value={monkey.traits.curiosity}
          />

          <Meter
            label="Sociability"
            value={monkey.traits.sociability}
          />

          <Meter
            label="Memory"
            value={monkey.traits.memory}
          />

          <Meter
            label="Aggression"
            value={monkey.traits.aggression}
          />
        </section>
      </aside>
    )
  }

  if (tourist) {
    return (
      <aside className="panel inspector-panel">
        <div className="panel__header">
          <div>
            <div className="panel__eyebrow">
              TOURIST #{String(tourist.id).padStart(3, '0')}
            </div>

            <h2>
              {tourist.name}
            </h2>
          </div>

          <button
            type="button"
            className="icon-button"
            onClick={onCloseTourist}
          >
            ×
          </button>
        </div>

        <div className="entity-summary">
          <div className="entity-avatar">
            🧍
          </div>

          <div>
            <div className="entity-meta">
              Tourist
            </div>

            <strong>
              Value {tourist.value}
            </strong>

            <div
              className={
                tourist.alive
                  ? 'status status--alive'
                  : 'status status--dead'
              }
            >
              <span />

              {tourist.alive
                ? 'Active'
                : 'Inactive'}
            </div>
          </div>
        </div>

        <section className="panel-section">
          <div className="panel-section__title">
            Details
          </div>

          <div className="detail-row">
            <span>Position</span>

            <strong>
              {tourist.x}, {tourist.y}
            </strong>
          </div>

          <div className="detail-row">
            <span>Total value</span>

            <strong>
              {tourist.value}
            </strong>
          </div>
        </section>

        <section className="panel-section">
          <div className="panel-section__title">
            Possessions
          </div>

          <div className="item-list">
            {tourist.items.length === 0 ? (
              <p className="panel-copy">
                No possessions.
              </p>
            ) : (
              tourist.items.map(
                (item, index) => (
                  <div
                    className="item-row"
                    key={`${item.name}-${index}`}
                  >
                    <span>
                      {item.name}
                    </span>

                    <strong>
                      {item.value}
                    </strong>
                  </div>
                ),
              )
            )}
          </div>
        </section>
      </aside>
    )
  }

  return (
    <aside className="panel inspector-panel inspector-panel--empty">
      <div className="panel__header">
        <div>
          <div className="panel__eyebrow">
            INSPECTOR
          </div>

          <h2>
            No Selection
          </h2>
        </div>
      </div>

      <div className="inspector-empty">
        <div className="inspector-empty__icon">
          ◎
        </div>

        <strong>
          Select an agent
        </strong>

        <p>
          Click a monkey or tourist on the map to inspect
          its current state.
        </p>
      </div>
    </aside>
  )
}

export default EntityInspector