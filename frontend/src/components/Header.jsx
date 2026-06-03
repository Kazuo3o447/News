export default function Header({ activePage, onNavigate }) {
  const navItems = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'settings',  label: 'Einstellungen' },
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
              className={`header__nav-btn ${activePage === key ? 'header__nav-btn--active' : ''}`}
              onClick={() => onNavigate(key)}
            >
              {label}
            </button>
          ))}
        </nav>

        <div className="header__meta">
          <span className="header__status-dot" />
          <span>Live</span>
        </div>
      </div>
    </header>
  )
}
