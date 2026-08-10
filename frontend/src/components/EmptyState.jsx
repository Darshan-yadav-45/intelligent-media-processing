export default function EmptyState({ message, actionLabel, onAction }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">🗂️</div>
      <p>{message}</p>
      {actionLabel && onAction && (
        <button className="btn btn-primary" onClick={onAction}>{actionLabel}</button>
      )}
    </div>
  );
}
