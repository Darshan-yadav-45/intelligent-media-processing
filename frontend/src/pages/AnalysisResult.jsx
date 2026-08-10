import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { imagesApi } from "../services/api.js";

function CheckRow({ label, ok, detail, confidence }) {
  return (
    <div className="check-row">
      <div className="check-row-main">
        <span className={ok ? "check-icon check-ok" : "check-icon check-warn"}>
          {ok ? "✓" : "⚠"}
        </span>
        <span className="check-label">{label}</span>
      </div>
      <div className="check-row-detail">
        {detail}
        {confidence != null && <span className="confidence-pill">{Math.round(confidence * 100)}%</span>}
      </div>
    </div>
  );
}

// Wording deliberately avoids absolute claims ("100% genuine") in favor of
// hedged, review-oriented language, per the assignment's guidance.
function assessmentLine(label, isIssue, okText, issueText) {
  return { label, text: isIssue ? issueText : okText, ok: !isIssue };
}

export default function AnalysisResult() {
  const { processingId } = useParams();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    imagesApi.result(processingId)
      .then(({ data }) => setResult(data))
      .catch(() => setError("Could not load analysis result."));
  }, [processingId]);

  if (error) return <div className="alert alert-error">{error}</div>;
  if (!result) return <div className="skeleton-block" />;

  const { image, analysis } = result;
  if (!analysis) {
    return <div className="alert alert-info">Analysis is not yet available for this image.</div>;
  }

  const hasVehicleNumber = !!analysis.vehicle_number.value;
  const hasRecognizedState = analysis.vehicle_state.state && analysis.vehicle_state.state !== "Unknown";

  const assessmentRows = [
    assessmentLine("Image Quality", analysis.blur.is_blurry || analysis.brightness.is_low_light, "Good", "Requires manual review"),
    assessmentLine("Vehicle Number", !hasVehicleNumber, analysis.vehicle_number.value, "Not detected"),
    assessmentLine("Registration State", !hasRecognizedState, analysis.vehicle_state.state, "Unknown"),
    assessmentLine("Duplicate", analysis.duplicate.is_duplicate, "No", "Possible duplicate"),
    assessmentLine("Low Light", analysis.brightness.is_low_light, "No", "Yes"),
    assessmentLine("Blur", analysis.blur.is_blurry, "No", "Yes"),
    assessmentLine("OCR", !hasVehicleNumber, "Detected", "Low confidence / not detected"),
    assessmentLine("Suspicious Editing", analysis.tampering.detected, "Not detected", "Possible issue detected"),
  ];

  return (
    <div className="result-page">
      <div className="page-header">
        <h1>Analysis Result</h1>
        <span className={analysis.overall_score === "GOOD" ? "badge badge-completed" : "badge badge-processing"}>
          {analysis.overall_score === "GOOD" ? "✓ GOOD" : "⚠ REVIEW REQUIRED"}
        </span>
      </div>

      <div className="result-grid">
        <div className="result-image-panel">
          <div className="result-image-placeholder">{image.filename}</div>
          <p className="dropzone-hint">{image.width}×{image.height} · {(image.file_size / 1024).toFixed(0)} KB</p>

          <div className="panel vehicle-info-card">
            <h3>Vehicle Information</h3>
            <div className="vehicle-info-row">
              <span className="profile-label">Number Plate</span>
              <span className="vehicle-info-value">{analysis.vehicle_number.value || "Not detected"}</span>
            </div>
            <div className="vehicle-info-row">
              <span className="profile-label">Registration State</span>
              <span className="vehicle-info-value">🇮🇳 {analysis.vehicle_state.state}</span>
            </div>
            <div className="vehicle-info-row">
              <span className="profile-label">State Code</span>
              <span className="vehicle-info-value">{analysis.vehicle_state.state_code || "—"}</span>
            </div>
            <div className="vehicle-info-row">
              <span className="profile-label">Format</span>
              <span className={analysis.vehicle_number.valid_format ? "check-ok" : "check-warn"}>
                {analysis.vehicle_number.valid_format ? "✓ Valid" : "⚠ Invalid / not detected"}
              </span>
            </div>
            <div className="vehicle-info-row">
              <span className="profile-label">Detection Confidence</span>
              <span className="confidence-pill">{Math.round((analysis.vehicle_state.confidence || 0) * 100)}%</span>
            </div>
            <div className="vehicle-info-row">
              <span className="profile-label">OCR Confidence</span>
              <span className="confidence-pill">{Math.round((analysis.ocr.confidence || 0) * 100)}%</span>
            </div>
            <p className="disclaimer">
              "Registration State" reflects where the number plate was issued —
              it is not the vehicle's current physical location.
            </p>
          </div>
        </div>

        <div className="result-details-panel">
          <h3>Image Quality</h3>
          <CheckRow label="Blur" ok={!analysis.blur.is_blurry} detail={`Score: ${analysis.blur.score}`} confidence={analysis.blur.confidence} />
          <CheckRow label="Brightness" ok={!analysis.brightness.is_low_light} detail={`Score: ${analysis.brightness.score}`} confidence={analysis.brightness.confidence} />

          <h3>Duplicate</h3>
          <CheckRow
            label="Duplicate Check"
            ok={!analysis.duplicate.is_duplicate}
            detail={analysis.duplicate.is_duplicate ? `Possible duplicate of a previous upload (${Math.round((analysis.duplicate.similarity || 0) * 100)}%)` : "No duplicate found"}
          />

          <h3>OCR</h3>
          <div className="check-row">
            <div className="check-row-main"><span className="check-label">Detected Text</span></div>
            <div className="check-row-detail">{analysis.ocr.text || "—"}</div>
          </div>
          <div className="check-row">
            <div className="check-row-main"><span className="check-label">Vehicle Number</span></div>
            <div className="check-row-detail">{analysis.vehicle_number.value || "—"}</div>
          </div>
          <CheckRow label="Format" ok={!!analysis.vehicle_number.valid_format} detail={analysis.vehicle_number.valid_format ? "Likely valid format" : "Invalid / not detected"} />

          <h3>Heuristic Checks</h3>
          <CheckRow label="Screenshot" ok={!analysis.screenshot.detected} detail={analysis.screenshot.detected ? "Possible screenshot" : "Not detected"} confidence={analysis.screenshot.confidence} />
          <CheckRow label="Photo of Photo" ok={!analysis.photo_of_photo.detected} detail={analysis.photo_of_photo.detected ? "Possible photo-of-photo" : "Not detected"} confidence={analysis.photo_of_photo.confidence} />
          <CheckRow label="Possible Tampering" ok={!analysis.tampering.detected} detail={analysis.tampering.detected ? "Potential issue detected" : "Not detected"} confidence={analysis.tampering.confidence} />

          <h3>Image Assessment</h3>
          <div className="assessment-summary">
            <div className="assessment-overall">
              Overall Status: <strong>{analysis.overall_score === "GOOD" ? "✓ GOOD" : "⚠ Requires manual review"}</strong>
            </div>
            {assessmentRows.map((row) => (
              <div className="check-row" key={row.label}>
                <span className="check-label">{row.label}</span>
                <span className={row.ok ? "check-ok" : "check-warn"}>{row.text}</span>
              </div>
            ))}
          </div>

          <p className="disclaimer">
            These are heuristic checks and confidence scores, not guarantees. Vehicle number
            format validation and state detection do not confirm the registration is genuine,
            and never indicate the vehicle's current location.
          </p>
        </div>
      </div>
    </div>
  );
}
