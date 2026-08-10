import { Link } from "react-router-dom";
import PublicNavbar from "../components/PublicNavbar.jsx";
import SiteFooter from "../components/SiteFooter.jsx";

const FEATURE_CARDS = [
  { icon: "🧠", title: "AI Image Analysis", desc: "A structured, multi-check pipeline that runs on every uploaded image." },
  { icon: "🔍", title: "Blur Detection", desc: "Laplacian-variance based sharpness scoring." },
  { icon: "💡", title: "Low-Light Detection", desc: "Grayscale brightness analysis flags poorly lit shots." },
  { icon: "🔤", title: "OCR", desc: "Tesseract-powered text extraction from number plates." },
  { icon: "🚗", title: "Vehicle Number Validation", desc: "Regex-based Indian registration format checks." },
  { icon: "📍", title: "State Detection", desc: "Maps a valid plate prefix to its registration state." },
  { icon: "📑", title: "Duplicate Detection", desc: "Perceptual hashing catches near-identical re-uploads." },
  { icon: "⚠️", title: "Tampering Detection", desc: "Lightweight heuristics flag possible editing." },
];

const STEPS = [
  { step: "1", title: "Upload", desc: "Drag and drop a vehicle image, or browse to select one." },
  { step: "2", title: "AI Processing", desc: "The image is queued and processed asynchronously by a Celery worker." },
  { step: "3", title: "Analysis", desc: "Ten heuristic checks run: quality, duplicates, OCR, format, and more." },
  { step: "4", title: "Insights", desc: "Structured, confidence-scored results land on your dashboard." },
];

export default function Home() {
  return (
    <div className="public-page">
      <PublicNavbar />

      <section className="hero">
        <div className="hero-overlay" />
        <div className="hero-content">
          <span className="hero-eyebrow">AI-Powered Vehicle Inspection Platform</span>
          <h1>Intelligent Media Processing</h1>
          <p className="hero-subtitle">
            AI-powered image analysis for vehicle images, quality detection and number plate intelligence.
          </p>
          <div className="hero-actions">
            <Link to="/upload" className="btn btn-primary btn-lg">Upload Image</Link>
            <Link to="/dashboard" className="btn btn-glass btn-lg">Explore Dashboard</Link>
          </div>
        </div>
      </section>

      <section className="section" id="features">
        <div className="section-header">
          <h2>Key Features</h2>
          <p>Ten explainable checks, not a black box.</p>
        </div>
        <div className="feature-grid">
          {FEATURE_CARDS.map((f) => (
            <div className="feature-card glass-card" key={f.title}>
              <div className="feature-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section section-alt">
        <div className="section-header">
          <h2>How It Works</h2>
        </div>
        <div className="steps-grid">
          {STEPS.map((s) => (
            <div className="step-card" key={s.step}>
              <div className="step-number">{s.step}</div>
              <h3>{s.title}</h3>
              <p>{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section stats-section">
        <div className="stats-grid">
          <div className="stat-block">
            <div className="stat-block-value">10+</div>
            <div className="stat-block-label">Image Checks</div>
          </div>
          <div className="stat-block">
            <div className="stat-block-value">8+</div>
            <div className="stat-block-label">AI / Computer Vision Features</div>
          </div>
          <div className="stat-block">
            <div className="stat-block-value">36</div>
            <div className="stat-block-label">States &amp; UTs Recognized</div>
          </div>
          <div className="stat-block">
            <div className="stat-block-value">99%</div>
            <div className="stat-block-label">API Availability Target</div>
          </div>
        </div>
      </section>

      <section className="section" id="state-intelligence">
        <div className="state-intel-panel glass-card">
          <div>
            <span className="hero-eyebrow">Vehicle Registration Intelligence</span>
            <h2>Automatic state detection from number plates</h2>
            <p>
              Once OCR reads a number plate and it passes format validation, the
              system automatically identifies the registration state encoded in
              the plate's prefix — e.g. <strong>KA05MN1234 → Karnataka</strong>.
              This reflects where the plate was registered, not where the
              vehicle currently is.
            </p>
            <Link to="/analytics" className="btn btn-primary">View State Analytics</Link>
          </div>
        </div>
      </section>

      <section className="section cta-section">
        <div className="cta-card">
          <h2>Ready to analyze your vehicle images?</h2>
          <Link to="/upload" className="btn btn-primary btn-lg">Upload Image</Link>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}
