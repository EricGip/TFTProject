import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

export default function LeaderboardPage() {
  const [players, setPlayers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/leaderboard')
      .then(r => r.json())
      .then(data => { setPlayers(data.players || []); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  if (loading) return <div className="loading">Loading leaderboard…</div>
  if (error) return <div className="error-box">{error}</div>

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Challenger Leaderboard</h1>
        <p className="page-subtitle">{players.length} players tracked · click a row to see match history</p>
      </div>

      <div className="leaderboard-table">
        <div className="table-header">
          <span>Rank</span>
          <span>Player</span>
          <span>LP</span>
          <span className="winrate-col">Win Rate</span>
          <span className="wl-col">W / L</span>
        </div>

        {players.map(p => {
          const wr = p.win_rate != null ? Number(p.win_rate) : null
          const wrClass = wr == null ? '' : wr >= 60 ? 'winrate-high' : wr >= 50 ? 'winrate-mid' : 'winrate-low'
          return (
            <Link
              key={p.riot_id || p.rank}
              to={`/player/${encodeURIComponent(p.riot_id)}`}
              className="table-row"
            >
              <span className="rank-badge">#{p.rank}</span>
              <span className="player-name">{p.riot_id || '—'}</span>
              <span className="lp-value">{p.league_points?.toLocaleString()} LP</span>
              <span className={`winrate-value winrate-col ${wrClass}`}>
                {wr != null ? `${wr}%` : '—'}
              </span>
              <span className="wl-value wl-col">{p.wins}W {p.losses}L</span>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
