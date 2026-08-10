import PublicNavbar from "../components/PublicNavbar.jsx";
import SiteFooter from "../components/SiteFooter.jsx";

export default function About() {
  return (
    <div className="public-page">
      <PublicNavbar />
      <section className="section about-section">
        <div className="section-header">
          <h2>About MediaIntel AI</h2>
          <p>An asynchronous image analysis pipeline for vehicle images.</p>
        </div>
        <div className="panel about-panel">
          <p>
            MediaIntel AI runs uploaded images through a battery of heuristic
            checks — blur, brightness, duplicate detection, OCR, Indian
            vehicle-number format validation, registration-state detection,
            screenshot/photo-of-photo heuristics, EXIF metadata, and a basic
            tampering heuristic — and surfaces the results with confidence
            scores rather than binary pass/fail verdicts.
          </p>
          <p>
            These are heuristic, explainable checks, not forensic-grade fraud
            detection or a claim of vehicle authenticity. Registration-state
            detection identifies where a plate was registered, never where the
            vehicle currently is.
          </p>
        </div>
      </section>
      <SiteFooter />
    </div>
  );
}
