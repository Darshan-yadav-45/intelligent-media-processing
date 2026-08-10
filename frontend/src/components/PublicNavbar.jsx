import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function PublicNavbar() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <header className="public-navbar">
      <div className="public-navbar-inner">
        <Link to="/" className="public-brand">
          <span className="public-brand-mark">MI</span>
          MediaIntel AI
        </Link>

        <button className="navbar-toggle" onClick={() => setOpen((o) => !o)} aria-label="Toggle navigation">
          ☰
        </button>

        <nav className={"public-nav-links" + (open ? " open" : "")}>
          <NavLink to="/" end onClick={() => setOpen(false)}>Home</NavLink>
          <NavLink to="/dashboard" onClick={() => setOpen(false)}>Dashboard</NavLink>
          <NavLink to="/upload" onClick={() => setOpen(false)}>Upload</NavLink>
          <NavLink to="/history" onClick={() => setOpen(false)}>History</NavLink>
          <NavLink to="/analytics" onClick={() => setOpen(false)}>Analytics</NavLink>
          <NavLink to="/about" onClick={() => setOpen(false)}>About</NavLink>

          <div className="public-nav-auth">
            {user ? (
              <>
                <Link to="/profile" className="public-nav-user">{user.name}</Link>
                <button className="btn btn-secondary" onClick={logout}>Logout</button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-secondary">Login</Link>
                <Link to="/register" className="btn btn-primary">Register</Link>
              </>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
}
