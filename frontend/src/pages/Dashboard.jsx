import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { analyticsApi, imagesApi } from "../services/api.js";
import Card from "../components/Card.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import EmptyState from "../components/EmptyState.jsx";

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const [summaryRes, imagesRes] = await Promise.all([
          analyticsApi.summary(),
          imagesApi.list({ page: 1, page_size: 5 }),
        ]);
        if (mounted) {
          setSummary(summaryRes.data);
          setRecent(imagesRes.data.items);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, []);

  if (loading) return <div className="skeleton-block" />;

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <Link to="/upload" className="btn btn-primary">Upload Image</Link>
      </div>

      <div className="stat-grid">
        <Card title="Total Uploads" value={summary?.total_uploads ?? 0} />
        <Card title="Completed" value={summary?.completed ?? 0} />
        <Card title="Processing" value={summary?.processing ?? 0} />
        <Card title="Failed" value={summary?.failed ?? 0} />
        <Card title="Duplicate Images" value={summary?.duplicate_count ?? 0} />
        <Card title="Blurry Images" value={summary?.blurry_count ?? 0} />
        <Card title="Low-Light Images" value={summary?.low_light_count ?? 0} />
        <Card title="Suspicious Images" value={summary?.suspicious_count ?? 0} />
      </div>

      <section className="panel">
        <h2>Recent Uploads</h2>
        {recent.length === 0 ? (
          <EmptyState message="No images uploaded yet." actionLabel="Upload your first image" onAction={() => navigate("/upload")} />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Status</th>
                <th>Vehicle Number</th>
                <th>Uploaded</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {recent.map((img) => (
                <tr key={img.processing_id}>
                  <td>{img.filename}</td>
                  <td><StatusBadge status={img.status} /></td>
                  <td>{img.vehicle_number || "—"}</td>
                  <td>{new Date(img.created_at).toLocaleString()}</td>
                  <td>
                    <Link to={`/processing/${img.processing_id}`}>View</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
