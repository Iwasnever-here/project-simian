import type { SimulationEvent } from '../App'

type Props = {
  events?: SimulationEvent[]
}

const labels: Record<string, string> = {
  birth: 'Birth',
  death: 'Death',
  social: 'Social',
  tourist: 'Tourist',
  tourist_arrival: 'Tourist',
}

function EventFeed({
  events = [],
}: Props) {
  const safeEvents =
    Array.isArray(events) ? events : []

  const visibleEvents =
    safeEvents.slice(0, 6)

  return (
    <section className="event-feed">
      <div className="event-feed__header">
        <div>
          <span className="panel__eyebrow">
            LIVE WORLD
          </span>

          <strong>
            Events Feed
          </strong>
        </div>

        <span className="event-feed__count">
          {safeEvents.length} events
        </span>
      </div>

      <div className="event-feed__list">
        {visibleEvents.length === 0 ? (
          <div className="event-feed__empty">
            No events yet.
          </div>
        ) : (
          visibleEvents.map((event) => (
            <article
              className="event-card"
              key={event.id}
            >
              <span
                className={
                  `event-card__icon event-card__icon--${event.type}`
                }
              >
                {event.type === 'birth'
                  ? '●'
                  : event.type === 'death'
                    ? '×'
                    : event.type.includes('tourist')
                      ? '◆'
                      : '○'}
              </span>

              <div className="event-card__body">
                <div className="event-card__meta">
                  <strong>
                    {labels[event.type] ??
                      event.type}
                  </strong>

                  <span>
                    Day {event.day}
                  </span>
                </div>

                <p>
                  {event.message}
                </p>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  )
}

export default EventFeed