import TraitBadge from './TraitBadge'
import UnitChip from './UnitChip'

const PLACEMENT_COLORS = {
  1: '#FFD700',
  2: '#4A9EFF',
  3: '#34D399',
  4: '#A3A3A3',
}

function placementColor(n) {
  return PLACEMENT_COLORS[n] || '#6B7280'
}

function placementLabel(n) {
  const suffix = { 1: 'st', 2: 'nd', 3: 'rd' }[n] || 'th'
  return `#${n}${suffix}`
}

function timeAgo(iso) {
  if (!iso) return ''
  const secs = Math.floor((Date.now() - new Date(iso)) / 1000)
  if (secs < 60) return 'just now'
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function MatchCard({ match }) {
  const color = placementColor(match.placement)
  const units = [...(match.units || [])].sort(
    (a, b) => (b.rarity - a.rarity) || (b.tier - a.tier)
  )
  const traits = (match.traits || []).filter(t => t.tier > 0).sort(
    (a, b) => b.tier - a.tier
  )

  return (
    <div className="match-card">
      <div className="match-placement-bar" style={{ backgroundColor: color }} />
      <div className="match-inner">
        <div className="match-meta">
          <span className="placement-badge" style={{ color }}>
            {placementLabel(match.placement)}
          </span>
          <span className="match-time">{timeAgo(match.fetched_at)}</span>
        </div>

        {traits.length > 0 && (
          <div className="traits-row">
            {traits.map((t, i) => <TraitBadge key={i} trait={t} />)}
          </div>
        )}

        <div className="units-row">
          {units.map((u, i) => <UnitChip key={i} unit={u} />)}
        </div>
      </div>
    </div>
  )
}
