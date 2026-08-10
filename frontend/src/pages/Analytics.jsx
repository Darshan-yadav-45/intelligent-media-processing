import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { analyticsApi } from "../services/api.js";
import Card from "../components/Card.jsx";
import EmptyState from "../components/EmptyState.jsx";
import { STATE_FILTER_OPTIONS } from "../utils/indianStates.js";

const STATUS_COLORS = { Completed: "#16a34a", Processing: "#2563eb", Failed: "#dc2626", Pending: "#f59e0b" };
const STATE_CHART_COLORS = ["#2563eb", "#0ea5e9", "#16a34a", "#f59e0b", "#dc2626", "#8b5cf6", "#0891b2", "#ea580c"];
const TOP_N_STATES = 7;

export default function Analytics() {
  const [summary, setSummary] = useState(null);
  const [stateData, setStateData] = useState(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [stateFilter, setStateFilter] = useState("All States");

  useEffect(() => {
    analyticsApi.summary().then(({ data }) => setSummary(data));
  }, []);

  useEffect(() => {
    analyticsApi.stateWise({
      status: statusFilter || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }).then(({ data }) => setStateData(data));
  }, [statusFilter, dateFrom, dateTo]);

  const handleExport = () => {
    analyticsApi.exportStateWiseCsv({
      status: statusFilter || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    });
  };

  if (!summary) return <div className="skeleton-block" />;

  const statusData = [
    { name: "Completed", value: summary.completed },
    { name: "Processing", value: summary.processing },
    { name: "Failed", value: summary.failed },
    { name: "Pending", value: summary.pending },
  ];

  const qualityData = [
    { name: "Blurry", value: summary.blurry_count },
    { name: "Low-Light", value: summary.low_light_count },
    { name: "Duplicate", value: summary.duplicate_count },
    { name: "Suspicious", value: summary.suspicious_count },
  ];

  const allStates = stateData?.by_state || [];
  const filteredStates = stateFilter !== "All States"
    ? allStates.filter((s) => s.state === stateFilter)
    : allStates;

  const topStates = filteredStates.slice(0, TOP_N_STATES);
  const othersCount = filteredStates.slice(TOP_N_STATES).reduce((sum, s) => sum + s.count, 0);
  const stateChartData = othersCount > 0 ? [...topStates, { state: "Others", count: othersCount }] : topStates;

  return (
    <div>
      <div className="page-header">
        <h1>Analytics</h1>
      </div>

      <div className="stat-grid">
        <Card title="Total Uploads" value={summary.total_uploads} />
        <Card title="Success Rate" value={`${Math.round(summary.success_rate * 100)}%`} />
        <Card title="Failure Rate" value={`${Math.round(summary.failure_rate * 100)}%`} />
        <Card title="Avg Processing Time" value={summary.avg_processing_time_seconds ? `${summary.avg_processing_time_seconds}s` : "—"} />
        <Card title="Avg Blur Score" value={summary.avg_blur_score ?? "—"} />
        <Card title="Duplicate Rate" value={`${Math.round(summary.duplicate_rate * 100)}%`} />
        <Card title="Low-Light Rate" value={`${Math.round(summary.low_light_rate * 100)}%`} />
        <Card title="OCR Detection Rate" value={`${Math.round(summary.ocr_detection_rate * 100)}%`} />
      </div>

      <div className="charts-grid">
        <div className="panel chart-panel">
          <h2>Processing Status Distribution</h2>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={statusData} dataKey="value" nameKey="name" outerRadius={90} label>
                {statusData.map((entry) => (
                  <Cell key={entry.name} fill={STATUS_COLORS[entry.name] || "#94a3b8"} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="panel chart-panel">
          <h2>Image Quality Issues</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={qualityData}>
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <section className="panel state-analytics-panel">
        <div className="page-header">
          <h2>State-wise Vehicle Analysis</h2>
          <button className="btn btn-secondary" onClick={handleExport}>Export State Analysis (CSV)</button>
        </div>

        <form className="filters-bar filters-bar-wrap" onSubmit={(e) => e.preventDefault()}>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          <select value={stateFilter} onChange={(e) => setStateFilter(e.target.value)}>
            {STATE_FILTER_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </form>

        {!stateData || filteredStates.length === 0 ? (
          <EmptyState message="No vehicle numbers detected yet for the selected filters." />
        ) : (
          <>
            <div className="stat-grid">
              <Card title="Total Vehicles Detected" value={filteredStates.reduce((sum, s) => sum + s.count, 0)} />
              <Card
                title="Top State"
                value={filteredStates[0]?.state || "—"}
                hint={filteredStates[0] ? `${filteredStates[0].count} vehicles` : undefined}
              />
            </div>

            <div className="charts-grid">
              <div className="panel chart-panel">
                <h3>Vehicles by State</h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={stateChartData}>
                    <XAxis dataKey="state" angle={-20} textAnchor="end" height={60} interval={0} tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="panel chart-panel">
                <h3>State Distribution</h3>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie data={stateChartData} dataKey="count" nameKey="state" outerRadius={90} label>
                      {stateChartData.map((entry, idx) => (
                        <Cell key={entry.state} fill={STATE_CHART_COLORS[idx % STATE_CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="state-ranking-grid">
              {filteredStates.map((s, idx) => (
                <div className="state-rank-card" key={s.state}>
                  <span className="state-rank-index">#{idx + 1}</span>
                  <span className="state-rank-name">{s.state}</span>
                  <span className="state-rank-count">{s.count}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
