const STATUS_STYLES = {
  pending: { label: "Pending", className: "badge badge-pending" },
  processing: { label: "Processing", className: "badge badge-processing" },
  completed: { label: "Completed", className: "badge badge-completed" },
  failed: { label: "Failed", className: "badge badge-failed" },
};

export default function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || { label: status, className: "badge" };
  return <span className={style.className}>{style.label}</span>;
}
