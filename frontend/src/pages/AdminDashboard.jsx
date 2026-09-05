import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/client";

function errorMessage(error, fallback) {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  return fallback;
}

const TABS = [
  { key: "PENDING_REVIEW", label: "Pending Review" },
  { key: "ACTIVE", label: "Active" },
  { key: "DRAFT", label: "Draft" },
  { key: "ALL", label: "All Profiles" },
];

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [tab, setTab] = useState("PENDING_REVIEW");
  const [search, setSearch] = useState("");
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const loadStats = async () => {
    try {
      const response = await api.get("/api/admin/stats");
      setStats(response.data);
    } catch {
      // Stats are a nice-to-have; a failure here shouldn't block the profile list.
    }
  };

  const loadProfiles = async (activeTab, searchTerm) => {
    setLoading(true);
    setError("");
    try {
      let response;
      if (activeTab === "PENDING_REVIEW" && !searchTerm) {
        response = await api.get("/api/admin/profiles/pending");
      } else {
        const params = {};
        if (activeTab !== "ALL") params.status_filter = activeTab;
        if (searchTerm) params.search = searchTerm;
        response = await api.get("/api/admin/profiles", { params });
      }
      setProfiles(response.data);
    } catch (err) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        setError(errorMessage(err, "Admin access required"));
      } else {
        setError(errorMessage(err, "Unable to load profiles"));
      }
    } finally {
      setLoading(false);
    }
  };

  const refresh = () => {
    loadStats();
    loadProfiles(tab, search);
  };

  useEffect(() => {
    loadStats();
  }, []);

  useEffect(() => {
    loadProfiles(tab, search);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  const onSearchSubmit = (e) => {
    e.preventDefault();
    loadProfiles(tab, search);
  };

  return (
    <main className="page wide">
      <div className="page-header">
        <div>
          <h1>Admin Dashboard</h1>
          <p>Review, approve and manage every member profile on MauryaShaadi.com.</p>
        </div>
        <button onClick={refresh}>Refresh</button>
      </div>

      {stats && (
        <div className="stat-grid">
          <div className="card stat-card">
            <span className="stat-label">Total Profiles</span>
            <strong className="stat-value">{stats.total}</strong>
          </div>
          <div className="card stat-card stat-pending">
            <span className="stat-label">Pending Review</span>
            <strong className="stat-value">{stats.pending_review}</strong>
          </div>
          <div className="card stat-card stat-active">
            <span className="stat-label">Active</span>
            <strong className="stat-value">{stats.active}</strong>
          </div>
          <div className="card stat-card stat-draft">
            <span className="stat-label">Draft</span>
            <strong className="stat-value">{stats.draft}</strong>
          </div>
        </div>
      )}

      <div className="card admin-toolbar">
        <div className="tabs">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              className={tab === t.key ? "tab active" : "tab"}
              onClick={() => setTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </div>
        <form className="admin-search" onSubmit={onSearchSubmit}>
          <input
            placeholder="Search by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit" className="secondary">Search</button>
        </form>
      </div>

      {loading && <div className="card"><p>Loading profiles...</p></div>}

      {!loading && error && <div className="card"><p className="message error">{error}</p></div>}

      {!loading && !error && profiles.length === 0 && (
        <div className="card">
          <h2>No profiles found</h2>
          <p className="muted">Nothing matches this filter right now.</p>
        </div>
      )}

      {!loading && !error && profiles.map((profile) => (
        <div className="card admin-profile-row" key={profile.user_id}>
          <div className="admin-profile-info">
            {profile.photo_url ? (
              <img
                className="admin-avatar"
                src={`${api.defaults.baseURL}${profile.photo_url}`}
                alt={profile.name || "Profile"}
              />
            ) : (
              <div className="admin-avatar admin-avatar-empty">No photo</div>
            )}

            <div>
              <h2>{profile.name || "Unnamed profile"}</h2>
              <p className="muted">
                User ID: {profile.user_id} · {profile.gender || "Gender not set"} · {profile.preferred_location || "Location not set"}
              </p>
              <span className={`status ${profile.status.toLowerCase()}`}>
                {profile.status.replace("_", " ")}
              </span>
            </div>
          </div>

          <button onClick={() => navigate(`/admin/profiles/${profile.user_id}`)}>
            Review Profile
          </button>
        </div>
      ))}

      <p><Link to="/dashboard">Back to Dashboard</Link></p>
    </main>
  );
}
