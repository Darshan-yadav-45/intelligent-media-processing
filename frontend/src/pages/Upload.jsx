import { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { imagesApi } from "../services/api.js";

const MAX_SIZE_MB = 10;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];

export default function Upload() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const validateAndSetFile = (selected) => {
    setError("");
    if (!selected) return;
    if (!ALLOWED_TYPES.includes(selected.type)) {
      setError("Unsupported file type. Please upload JPG, PNG, or WEBP.");
      return;
    }
    if (selected.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File exceeds the ${MAX_SIZE_MB}MB size limit.`);
      return;
    }
    setFile(selected);
    setPreview(URL.createObjectURL(selected));
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragActive(false);
    validateAndSetFile(e.dataTransfer.files?.[0]);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await imagesApi.upload(formData, (evt) => {
        setProgress(Math.round((evt.loaded * 100) / evt.total));
      });
      navigate(`/processing/${data.processing_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Upload Image</h1>
      </div>

      <div
        className={"dropzone" + (dragActive ? " dropzone-active" : "")}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        {preview ? (
          <img src={preview} alt="preview" className="dropzone-preview" />
        ) : (
          <>
            <div className="dropzone-icon">⬆️</div>
            <p>Drag & drop an image here, or click to browse</p>
            <p className="dropzone-hint">JPG, PNG, WEBP — up to {MAX_SIZE_MB}MB</p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          hidden
          onChange={(e) => validateAndSetFile(e.target.files?.[0])}
        />
      </div>

      {file && (
        <div className="file-meta">
          <span>{file.name}</span>
          <span>{(file.size / 1024).toFixed(0)} KB</span>
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}

      {uploading && (
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      )}

      <button className="btn btn-primary" onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? "Uploading..." : "Upload & Analyze"}
      </button>
    </div>
  );
}
