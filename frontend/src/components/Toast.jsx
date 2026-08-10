export default function Toast({ message, type = "info", onClose }) {
  if (!message) return null;
  return (
    <div className={`toast toast-${type}`} onClick={onClose}>
      {message}
    </div>
  );
}
