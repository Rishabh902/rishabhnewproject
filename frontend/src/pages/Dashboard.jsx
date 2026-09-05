import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";

function errorMessage(error, fallback) {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return detail?.message || fallback;
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [matches, setMatches] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setMessage("");
    try {
      const profileResponse = await api.get("/api/profiles/me");
      setProfile(profileResponse.data);
      if (profileResponse.data.status === "ACTIVE") {
        const matchResponse = await api.get("/api/profiles/matches");
        setMatches(matchResponse.data);
      } else {
        setMatches([]);
      }
    } catch (error) {
      setMessage(errorMessage(error, "Unable to load dashboard"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) return <main className="page"><p>Loading dashboard...</p></main>;

  return (
    <main className="page wide">
      <div className="page-header">
        <div>
          <h1>Welcome, {profile?.name || "Member"}</h1>
          <p>User ID: {user?.id}</p>
        </div>
        <button onClick={logout}>Logout</button>
      </div>

      {message && <div className="card"><p className="error">{message}</p></div>}

      <section className="card">
        <h2>Profile status</h2>
        <span className={`status ${profile?.status?.toLowerCase()}`}>{profile?.status}</span>
        {profile?.status === "DRAFT" && <><p>Complete your profile and submit it for admin approval.</p><Link className="button" to="/complete-profile">Complete Profile</Link></>}
        {profile?.status === "PENDING_REVIEW" && <p>Your profile is waiting for admin review. Matching profiles will become available after approval.</p>}
        {profile?.status === "ACTIVE" && <><p>Your profile is approved. Matching profiles are now available below.</p><Link className="button" to="/matches">Open AI Matches</Link><Link className="button secondary" to="/interests">Interests</Link><Link className="button secondary" to="/shortlist">Shortlist</Link><Link className="button secondary" to="/notifications">Notifications</Link></>}
        {profile?.rejection_reason && <div className="notice"><strong>Admin requested changes:</strong><p>{profile.rejection_reason}</p><Link className="button" to="/complete-profile">Correct & Resubmit</Link></div>}
      </section>

      {profile?.status === "ACTIVE" && (
        <section>
          <div className="page-header"><div><h2>Matching profiles</h2><p className="muted">Only admin-approved ACTIVE profiles appear here.</p></div><button onClick={load}>Refresh</button></div>
          {matches.length === 0 ? <div className="card"><p>No matching profiles are available yet.</p></div> : <div className="match-grid">{matches.map((match) => <article className="card match-card" key={match.user_id}>
            {match.photo_url ? <img src={`${api.defaults.baseURL}${match.photo_url}`} alt={match.name || "Profile"} /> : <div className="match-photo-empty">No photo</div>}
            <h3>{match.name || "Member"}</h3>
            <p>{match.community || "Community not specified"}</p>
            <p>{match.preferred_location || "Location not specified"}</p>
            <p>{match.education || "Education not specified"}</p>
            <span className="status active">{match.compatibility_score}% match</span>
          </article>)}</div>}
        </section>
      )}
    </main>
  );
}
