import { useEffect, useRef, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../features/auth/AuthContext";
import { DoorExitIcon, MenuIcon } from "../shared/ui/icons";

const NAV_ITEMS = [
  { to: "/", end: true, label: "Создать" },
  { to: "/cloud", end: false, label: "Заметки" },
  { to: "/stats", end: false, label: "Статистика" },
];

export function Layout() {
  const { logout, username } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const location = useLocation();

  useEffect(() => setMenuOpen(false), [location.pathname]);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    }
    document.addEventListener("click", onDocClick);
    return () => document.removeEventListener("click", onDocClick);
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "0.8em 1.2em",
          borderBottom: "1px solid var(--border)",
          gap: "0.8em",
          position: "relative",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.6em" }} ref={menuRef}>
          <button
            type="button"
            className="icon-btn nav-mobile-trigger"
            title="Меню"
            aria-label="Меню"
            onClick={(e) => {
              e.stopPropagation();
              setMenuOpen((o) => !o);
            }}
          >
            <MenuIcon />
          </button>
          {menuOpen && (
            <div className="nav-dropdown">
              {NAV_ITEMS.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => (isActive ? "active" : undefined)}
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          )}

          <Link to="/" style={{ textDecoration: "none" }}>
            <strong style={{ color: "var(--text-h)", letterSpacing: "0.04em" }}>VENT</strong>
          </Link>
        </div>

        <nav className="nav-desktop" style={{ gap: "1.2em" }}>
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} style={navStyle}>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div style={{ display: "flex", gap: "0.8em", alignItems: "center" }}>
          <span className="muted" style={{ fontSize: "0.85em" }}>
            {username}
          </span>
          <button
            type="button"
            className="icon-btn icon-btn-danger"
            title="Выйти"
            aria-label="Выйти"
            onClick={logout}
          >
            <DoorExitIcon />
          </button>
        </div>
      </header>

      <main style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
        <Outlet />
      </main>
    </div>
  );
}

function navStyle({ isActive }: { isActive: boolean }) {
  return {
    textDecoration: "none",
    fontSize: "0.85em",
    color: isActive ? "var(--accent)" : "var(--text)",
    fontWeight: isActive ? 700 : 400,
  };
}
