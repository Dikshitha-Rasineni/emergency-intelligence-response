import { Link } from 'react-router-dom'
import SeverityBadge from './SeverityBadge'
import PriorityScore from './PriorityScore'
import { formatTime, shortId } from '../../utils/incidents'

export default function IncidentRow({ incident, selected, isNew, onSelect }) {
  const i = incident
  return (
    <li
      className={`inc inc--${i.severityKnown ? i.severity.toLowerCase() : 'unknown'}${selected ? ' is-selected' : ''}${isNew ? ' is-new' : ''}`}
      onMouseEnter={() => onSelect?.(i.id)}
      onFocus={() => onSelect?.(i.id)}
    >
      <PriorityScore value={i.priority} severity={i.severity} known={i.priorityKnown} />
      <div className="inc__main">
        <div className="inc__head">
          <Link to={`/incidents/${i.id}`} className="inc__id mono">{shortId(i.id)}</Link>
          <span className="inc__type">{i.type}</span>
          <SeverityBadge severity={i.severity} known={i.severityKnown} />
        </div>
        <div className="inc__facts">
          <span><b className="mono">{i.affected}</b> affected</span>
          <span><b className="mono">{i.injuries}</b> injured</span>
          <span className="inc__loc">{i.location}</span>
          <span className="mono inc__time">{formatTime(i.time)}</span>
        </div>
      </div>
    </li>
  )
}
