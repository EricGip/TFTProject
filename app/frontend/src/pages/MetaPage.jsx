import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

function formatName(id) {
  const part = id.split('_').pop()
  return part.replace(/([A-Z])/g, ' $1').trim()
}

export default function MetaPage() {
  const [tab, setTab] = useState('units')
  const [units, setUnits] = useState([])
  const [traits, setTraits] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      fetch('/api/meta/units').then(r => r.json()),
      fetch('/api/meta/traits').then(r => r.json()),
    ])
      .then(([uData, tData]) => {
        setUnits(uData.units || [])
        setTraits(tData.traits || [])
        setLoading(false)
      })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  if (loading) return <div className="loading">Loading meta data…</div>
  if (error) return <div className="error-box">{error}</div>

  const items = tab === 'units' ? units : traits
  const maxCount = items.length > 0 ? items[0].games_played : 1

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Meta Snapshot</h1>
        <p className="page-subtitle">
          Most played {tab} across all tracked Challenger matches
        </p>
      </div>

      <div className="meta-tabs">
        <button
          className={`tab-btn ${tab === 'units' ? 'active' : ''}`}
          onClick={() => setTab('units')}
        >
          Units
        </button>
        <button
          className={`tab-btn ${tab === 'traits' ? 'active' : ''}`}
          onClick={() => setTab('traits')}
        >
          Traits
        </button>
      </div>

      <div className="frequency-list">
        {items.map((item, i) => {
          const name = tab === 'units'
            ? formatName(item.character_id)
            : formatName(item.trait_name)
          const pct = Math.round((item.games_played / maxCount) * 100)
          const meta = tab === 'units'
            ? `Avg ★${item.avg_tier} · ${Number(item.avg_rarity || 0).toFixed(0)}-cost`
            : `Avg ${item.avg_num_units} units`
          const players = item.players || []

          return (
            <div key={i} className="freq-row">
              <div>
                <div className="freq-name">{name}</div>
                {players.length > 0 && (
                  <div className="players-tags">
                    {players.slice(0, 4).map((pid, j) => (
                      <Link
                        key={j}
                        to={`/player/${encodeURIComponent(pid)}`}
                        className="player-tag"
                      >
                        {pid}
                      </Link>
                    ))}
                    {players.length > 4 && (
                      <span className="player-tag player-tag-more">
                        +{players.length - 4} more
                      </span>
                    )}
                  </div>
                )}
              </div>
              <div className="freq-bar-wrapper">
                <div className="freq-bar" style={{ width: `${pct}%` }} />
              </div>
              <div className="freq-count">{item.games_played} games</div>
              <div className="freq-meta">{meta}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
