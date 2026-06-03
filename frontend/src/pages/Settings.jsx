import { useState, useEffect } from 'react'
import axios from 'axios'

export default function Settings() {
  const [feeds, setFeeds]           = useState([])
  const [loading, setLoading]       = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [message, setMessage]       = useState(null)

  useEffect(() => {
    axios.get('/api/feeds')
      .then(res => setFeeds(res.data.feeds || []))
      .finally(() => setLoading(false))
  }, [])

  async function handleRefresh() {
    setRefreshing(true)
    setMessage(null)
    try {
      await axios.post('/api/refresh')
      setMessage({ type: 'ok', text: 'Feed-Refresh wurde gestartet. Neue Artikel erscheinen in Kürze.' })
    } catch {
      setMessage({ type: 'err', text: 'Refresh konnte nicht ausgelöst werden.' })
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <>
      <header className="page-head">
        <div>
          <h1 className="page-head__title">Einstellungen</h1>
          <p className="page-head__subtitle">Konfigurierte RSS-Feeds und manuelle Steuerung der Pipeline.</p>
        </div>
      </header>

      <section className="card">
        <h2 className="card__title">Manuelle Aktualisierung</h2>
        <p className="card__subtitle">
          Stößt die RSS-Pipeline jetzt sofort an (läuft sonst automatisch alle 30 Minuten).
        </p>
        <button className="btn" onClick={handleRefresh} disabled={refreshing}>
          {refreshing ? '↻ Lädt …' : '↻ Feeds jetzt aktualisieren'}
        </button>
        {message && (
          <div className={`toast toast--${message.type}`}>{message.text}</div>
        )}
      </section>

      <section className="card">
        <h2 className="card__title">RSS-Feed-Quellen</h2>
        <p className="card__subtitle">
          {feeds.length} aktive Feeds aus Microsoft, DE- und EN-IT-Medien.
        </p>

        {loading ? (
          <p style={{ color: 'var(--gema-muted)' }}>Lädt …</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="feed-table">
              <thead>
                <tr>
                  <th>Quelle</th>
                  <th>Priorität</th>
                  <th>URL</th>
                </tr>
              </thead>
              <tbody>
                {feeds.map((feed, i) => (
                  <tr key={i}>
                    <td className="feed-table__name">{feed.name}</td>
                    <td>
                      <span className={`priority priority--${feed.priority}`}>
                        <span className="priority__dot" />
                        {feed.priority}
                      </span>
                    </td>
                    <td>
                      <a className="feed-table__url" href={feed.url}
                         target="_blank" rel="noopener noreferrer">{feed.url}</a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )
}
