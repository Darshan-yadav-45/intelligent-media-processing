import { Link } from "react-router-dom";

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-inner">
        <div className="footer-brand">
          <span className="public-brand-mark">MI</span>
          MediaIntel AI
        </div>

        <div className="footer-columns">
          <div className="footer-col">
            <h4>Product</h4>
            <Link to="/upload">Upload</Link>
            <Link to="/dashboard">Dashboard</Link>
          </div>
          <div className="footer-col">
            <h4>Features</h4>
            <Link to="/#features">AI Image Analysis</Link>
            <Link to="/#state-intelligence">State Detection</Link>
          </div>
          <div className="footer-col">
            <h4>Analytics</h4>
            <Link to="/analytics">Analytics Dashboard</Link>
            <Link to="/history">Image History</Link>
          </div>
          <div className="footer-col">
            <h4>Documentation</h4>
            <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API Docs</a>
            <Link to="/about">About</Link>
          </div>
          <div className="footer-col">
            <h4>Contact</h4>
            <a href="https://github.com" target="_blank" rel="noreferrer">GitHub</a>
            <a href="mailto:contact@example.com">Contact</a>
          </div>
        </div>
      </div>
      <div className="footer-bottom">
        © {new Date().getFullYear()} MediaIntel AI — Heuristic analysis, not a guarantee of authenticity.
      </div>
    </footer>
  );
}
