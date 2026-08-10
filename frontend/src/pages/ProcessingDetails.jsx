import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { imagesApi } from "../services/api.js";
import StatusBadge from "../components/StatusBadge.jsx";

const POLL_INTERVAL_MS = 2000;

export default function ProcessingDetails() {
  const { processingId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState("pending");
  const [error, setError] = useState("");
  const intervalRef = useRef(null);

  useEffect(() => {
    async function poll() {
      try {
        const { data } = await imagesApi.status(processingId);
        setStatus(data.status);
        if (data.status === "completed") {
          clearInterval(intervalRef.current);
          navigate(`/result/${processingId}`);
        } else if (data.status === "failed") {
          clearInterval(intervalRef.current);
          setError(data.error_message || "Processing failed.");
        }
      } catch (err) {
        clearInterval(intervalRef.current);
        setError("Could not fetch processing status.");
      }
    }

    poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(intervalRef.current);
  }, [processingId, navigate]);

  const handleRetry = async () => {
    setError("");
    setStatus("pending");
    await imagesApi.retry(processingId);
    intervalRef.current = setInterval(async () => {
      const { data } = await imagesApi.status(processingId);
      setStatus(data.status);
      if (data.status === "completed") {
        clearInterval(intervalRef.current);
        navigate(`/result/${processingId}`);
      } else if (data.status === "failed") {
        clearInterval(intervalRef.current);
        setError(data.error_message || "Processing failed again.");
      }
    }, POLL_INTERVAL_MS);
  };

  return (
    <div className="processing-page">
      <h1>Processing Image</h1>
      <p className="processing-id">Processing ID: {processingId}</p>

      <div className="processing-status-card">
        <StatusBadge status={status} />
        {status === "pending" || status === "processing" ? (
          <div className="spinner" />
        ) : null}
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
          <div style={{ marginTop: "12px" }}>
            <button className="btn btn-primary" onClick={handleRetry}>Retry</button>
          </div>
        </div>
      )}
    </div>
  );
}
