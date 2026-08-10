import { useAuth } from "../context/AuthContext.jsx";

export default function Profile() {
  const { user } = useAuth();

  return (
    <div>
      <div className="page-header">
        <h1>Profile</h1>
      </div>
      <div className="panel" style={{ maxWidth: "480px" }}>
        <div className="profile-row">
          <span className="profile-label">Name</span>
          <span>{user?.name}</span>
        </div>
        <div className="profile-row">
          <span className="profile-label">Email</span>
          <span>{user?.email}</span>
        </div>
        <div className="profile-row">
          <span className="profile-label">Member since</span>
          <span>{user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}</span>
        </div>
      </div>
    </div>
  );
}
