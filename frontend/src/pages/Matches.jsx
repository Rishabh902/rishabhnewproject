import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";

function errorMessage(error, fallback) {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return detail?.message || fallback;
}

const BREAKDOWN_LABELS = {
  location: "Location",
  profession: "Profession",
  qualification: "Qualification",
  age: "Age",
  height: "Height",
};

function MatchCard({ match }) {
  const base = api.defaults.baseURL;
  const breakdownEntries = Object.entries(match.match_breakdown || {});
  return <article className="card match-card">
    {match.photo_url ? <img src={`${base}${match.photo_url}`} alt={match.name || "Profile"} /> : <div className="match-photo-empty">No photo</div>}
    <div className="match-card-body">
      <div className="match-title-row"><h3>{match.name || "Member"}</h3><span className="score-badge">{match.compatibility_score}%</span></div>
      {match.relaxed_match && <span className="status pending_review">Outside exact preference</span>}
      <p>{match.preferred_location || "Location not specified"}</p><p>{match.profession || "Profession not specified"}</p><p>{match.education || "Qualification not specified"}</p>
      <div className="match-breakdown">
        {breakdownEntries.map(([key, value]) => (
          <div key={key}><span>{BREAKDOWN_LABELS[key] || key}</span><strong>{value}%</strong></div>
        ))}
      </div>
      <Link className="button" to={`/profile/${match.user_id}`}>View Profile</Link>
    </div>
  </article>;
}

export default function Matches() {
  const [recommendations, setRecommendations] = useState([]);
  const [actualMatches, setActualMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const base = api.defaults.baseURL;

  const loadMatches = async () => {
    setLoading(true); setMessage("");
    try {
      const [recommendationResponse, matchResponse] = await Promise.all([
        api.get("/api/profiles/matches"),
        api.get("/api/matches"),
      ]);
      setRecommendations(recommendationResponse.data);
      setActualMatches(matchResponse.data);
    } catch (error) { setMessage(errorMessage(error, "Unable to load matches")); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadMatches(); }, []);

  return <main className="page wide">
    <div className="page-header"><div><h1>Matches & Recommendations</h1><p className="muted">Recommendations are ranked using location (25%), profession (20%), qualification (20%), age fit (15%) and height fit (20%). Every ACTIVE profile is shown, ranked highest first.</p></div><button onClick={loadMatches}>Refresh</button></div>
    {loading && <div className="card"><p>Finding the best profiles...</p></div>}
    {message && <div className="card"><p className="error">{message}</p></div>}

    {!loading && <>
      <section>
        <div className="section-heading"><div><h2>My Matches</h2><p className="muted">These are confirmed matches created after an interest was accepted.</p></div></div>
        {actualMatches.length === 0 ? <div className="card"><p className="muted">No confirmed matches yet. Send an interest from a profile to get started.</p></div> : <div className="match-grid">{actualMatches.map(match => <article className="card match-card" key={match.id}>
          {match.other_user_photo_url ? <img src={`${base}${match.other_user_photo_url}`} alt={match.other_user_name || "Profile"}/> : <div className="match-photo-empty">No photo</div>}
          <div className="match-card-body"><h3>{match.other_user_name || "Member"}</h3><p>Confirmed match</p>{match.score != null && <span className="status active">{match.score}% compatibility</span>}<Link className="button" to={`/profile/${match.other_user_id}`}>View Profile</Link></div>
        </article>)}</div>}
      </section>

      <section>
        <div className="section-heading"><div><h2>Recommended Profiles</h2><p className="muted">Only ACTIVE/admin-approved profiles are included.</p></div></div>
        {recommendations.length === 0 ? <div className="card"><h2>No recommendations available</h2><p>There are no other ACTIVE approved profiles of a compatible gender yet.</p></div> : <><div className="card match-info"><strong>{recommendations.length} recommended profile{recommendations.length === 1 ? "" : "s"}</strong><span>Every ACTIVE/admin-approved profile is included, ranked by compatibility.</span></div><div className="match-grid">{recommendations.map(match => <MatchCard key={match.user_id} match={match}/>)}</div></>}
      </section>
    </>}
  </main>;
}
