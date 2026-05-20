import { Link, NavLink } from 'react-router-dom'

export default function NavBar() {
  return (
    <nav className="navbar">
      <Link to="/" className="nav-brand">TFT Challenger</Link>
      <div className="nav-links">
        <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
          Leaderboard
        </NavLink>
        <NavLink to="/meta" className={({ isActive }) => isActive ? 'active' : ''}>
          Meta
        </NavLink>
      </div>
    </nav>
  )
}
