import { BrowserRouter, Routes, Route } from 'react-router-dom'
import NavBar from './components/NavBar'
import LeaderboardPage from './pages/LeaderboardPage'
import PlayerPage from './pages/PlayerPage'
import MetaPage from './pages/MetaPage'

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <main className="container">
        <Routes>
          <Route path="/" element={<LeaderboardPage />} />
          <Route path="/player/:riotId" element={<PlayerPage />} />
          <Route path="/meta" element={<MetaPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
