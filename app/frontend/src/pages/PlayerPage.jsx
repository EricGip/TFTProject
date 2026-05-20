import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import MatchCard from '../components/MatchCard'

export default function PlayerPage() {
  const { riotId } = useParams()
  const [playerData, setPlayerData] = useState(null)
  const [matches, setMatches] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const encoded = encodeURIComponent(riotId)
    Promise.all([
      fetch(`/api/player/${encoded}`).then(r => r.json()),
      fetch(`/api/player/${encoded}/matches`).then(r => r.json()),
    ])
      .then(([pData, mData]) => {
        setPlayerData(pData.error ? null : pData)
        setMatches(mData.matches || [])
        setLoading(false)
      })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [riotId])

  if (loading) return <div className="loading">Loading player data…</div>
  if (error) return <div className="error-box">{error}</div>

  const wr = playerData?.win_rate != null ? Number(playerData.win_rate) : null

  return (
    <div>
      <Link to="/" className="back-btn">← Leaderboard</Link>

      {playerData && (
        <div className="player-header">
          <div className="player-rank-badge">#{playerData.rank}</div>
          <div className="player-info">
            <h1>{riotId}</h1>
            <div className="player-meta">
              <span>{playerData.league_points?.toLocaleString()} LP</span>
              <span>{playerData.wins}W {playerData.losses}L</span>
              {wr != null && <span>{wr}% WR</span>}
            </div>
          </div>
        </div>
      )}

      <div className="page-header">
        <h2 className="page-title" style={{ fontSize: '1.05rem' }}>
          Recent Matches ({matches.length})
        </h2>
      </div>

      {matches.length === 0 ? (
        <div className="error-box">No match data found for this player yet.</div>
      ) : (
        <div className="matches-list">
          {matches.map(match => (
            <MatchCard key={match.match_id} match={match} />
          ))}
        </div>
      )}
    </div>
  )
}
