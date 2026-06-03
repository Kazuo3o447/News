/**
 * F5 — Header: verschlankt. GEMA-Rot-Balken, flacher, Dark-Mode-Toggle, Ungelesen-Zahl.
 */
export default function Header({ activePage, onNavigate, kritischUnread = 0, darkMode, onToggleDark }) {
  const navItems = [
    { key: "dashboard", label: "Dashboard" },
    { key: "settings",  label: "Einstellungen" },
  ]

  return (
    <header className="header">
      <div className="header__inner">
        <div className="header__brand">
          <span className="header__logo-mark">IT</span>
          <span>News&nbsp;Hub</span>
        </div>

        <nav className="header__nav">
          {navItems.map(({ key, label }) => (
            <button
              key={key}
              className={`header__nav-btn${activePage === key ? " header__nav-btn--active" : ""}`}
              onClick={() => onNavigate(key)}
            >
              {label}
            </button>
          ))}
        </nav>

        <div className="header__meta">
          {kritischUnread > 0 && (
            <span className="header__unread-pill" title={`${kritischUnread} ungelesene kritische Meldungen`}>
              {kritischUnread} kritisch
            </span>
          )}
          <button
            className="header__dark-toggle"
            onClick={onToggleDark}
            title={darkMode ? "Hell-Modus" : "Dunkel-Modus"}
            aria-label="Dark Mode umschalten"
          >
            {darkMode ? "☀" : "☽"}
          </button>
        </div>
      </div>
    </header>
  )
}
