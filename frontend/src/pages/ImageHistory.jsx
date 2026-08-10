import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { imagesApi } from "../services/api.js";
import StatusBadge from "../components/StatusBadge.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { STATE_FILTER_OPTIONS } from "../utils/indianStates.js";

const PAGE_SIZE = 10;

export default function ImageHistory() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [stateFilter, setStateFilter] = useState("All States");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await imagesApi.list({
        page, page_size: PAGE_SIZE,
        search: search || undefined,
        status: statusFilter || undefined,
        state: stateFilter !== "All States" ? stateFilter : undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      });
      setItems(data.items);
      setTotal(data.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page, statusFilter, stateFilter, dateFrom, dateTo]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    load();
  };

  const handleDelete = async (processingId) => {
    if (!window.confirm("Delete this image and its analysis results?")) return;
    await imagesApi.remove(processingId);
    load();
  };

  const handleRetry = async (processingId) => {
    await imagesApi.retry(processingId);
    load();
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <div className="page-header">
        <h1>Image History</h1>
      </div>

      <form className="filters-bar filters-bar-wrap" onSubmit={handleSearch}>
        <input
          type="text" placeholder="Search filename..."
          value={search} onChange={(e) => setSearch(e.target.value)}
        />
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
        <select value={stateFilter} onChange={(e) => { setStateFilter(e.target.value); setPage(1); }}>
          {STATE_FILTER_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <input type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1); }} />
        <input type="date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(1); }} />
        <button className="btn btn-secondary" type="submit">Search</button>
      </form>

      {loading ? (
        <div className="skeleton-block" />
      ) : items.length === 0 ? (
        <EmptyState message="No images match your filters." />
      ) : (
        <>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Processing ID</th>
                  <th>Uploaded</th>
                  <th>Status</th>
                  <th>Issues</th>
                  <th>Vehicle Number</th>
                  <th>State</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((img) => (
                  <tr key={img.processing_id}>
                    <td>{img.filename}</td>
                    <td className="mono-cell">{img.processing_id.slice(0, 8)}…</td>
                    <td>{new Date(img.created_at).toLocaleDateString()}</td>
                    <td><StatusBadge status={img.status} /></td>
                    <td>
                      {[img.is_blurry && "Blurry", img.is_low_light && "Low-light", img.is_duplicate && "Duplicate"]
                        .filter(Boolean).join(", ") || "—"}
                    </td>
                    <td>{img.vehicle_number || "—"}</td>
                    <td>{img.state_name || "—"}</td>
                    <td className="actions-cell">
                      <Link to={img.status === "completed" ? `/result/${img.processing_id}` : `/processing/${img.processing_id}`}>View</Link>
                      {img.status === "failed" && (
                        <button className="link-btn" onClick={() => handleRetry(img.processing_id)}>Retry</button>
                      )}
                      <button className="link-btn link-danger" onClick={() => handleDelete(img.processing_id)}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button className="btn btn-secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
            <span>Page {page} of {totalPages}</span>
            <button className="btn btn-secondary" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</button>
          </div>
        </>
      )}
    </div>
  );
}
