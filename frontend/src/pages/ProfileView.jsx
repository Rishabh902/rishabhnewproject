import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api from "../api/client";

function errorMessage(error, fallback = "Something went wrong") {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return detail?.message || fallback;
}

export default function ProfileView() {
  const { userId } = useParams();
  const [profile, setProfile] = useState(null);
  const [shortlisted, setShortlisted] = useState(false);
  const [interest, setInterest] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const base = api.defaults.baseURL;

  const load = async () => {
    setError("");
    try {
      const [p, shortlist, sent, received] = await Promise.all([
        api.get(`/api/profiles/${userId}`),
        api.get("/api/shortlists"),
        api.get("/api/interests/sent"),
        api.get("/api/interests/received"),
      ]);
      setProfile(p.data);
      setShortlisted(shortlist.data.some(x => String(x.profile_user_id) === String(userId)));
      const found = [...sent.data, ...received.data].find(x => String(x.other_user_id || (String(x.sender_id) === String(userId) ? x.receiver_id : x.sender_id)) === String(userId));
      setInterest(found || null);
    } catch (err) { setError(errorMessage(err, "Unable to load profile")); }
  };

  useEffect(() => { load(); }, [userId]);

  const toggleShortlist = async () => {
    setBusy(true); setError("");
    try {
      if (shortlisted) { await api.delete(`/api/shortlists/${userId}`); setShortlisted(false); }
      else { await api.post("/api/shortlists", { profile_user_id: Number(userId) }); setShortlisted(true); }
    } catch (err) { setError(errorMessage(err, "Unable to update shortlist")); }
    finally { setBusy(false); }
  };

  const sendInterest = async () => {
    setBusy(true); setError("");
    try { const r = await api.post("/api/interests", { receiver_id: Number(userId) }); setInterest(r.data); }
    catch (err) { setError(errorMessage(err, "Unable to send interest")); }
    finally { setBusy(false); }
  };

  if (error && !profile) return <main className="page"><div className="card"><p className="error">{error}</p><Link className="button" to="/matches">Back to Matches</Link></div></main>;
  if (!profile) return <main className="page"><p>Loading profile...</p></main>;

  return <main className="page wide">
    <div className="page-header"><div><h1>{profile.name || "Member"}</h1><p className="muted">Approved profile</p></div><Link className="button" to="/matches">Back to Matches</Link></div>
    {error && <div className="card"><p className="error">{error}</p></div>}
    <section className="card profile-view">
      {profile.photo_url ? <img className="profile-view-photo" src={`${base}${profile.photo_url}`} alt={profile.name || "Profile"}/> : <div className="profile-view-empty">No photo</div>}
      <div className="profile-action-bar">
        <button onClick={toggleShortlist} disabled={busy}>{shortlisted ? "★ Remove Shortlist" : "☆ Add to Shortlist"}</button>
        {interest ? <span className={`status ${interest.status.toLowerCase()}`}>Interest: {interest.status}</span> : <button className="secondary" onClick={sendInterest} disabled={busy}>💌 Send Interest</button>}
        {interest?.status === "ACCEPTED" && <Link className="button" to="/notifications">Open Notifications</Link>}
      </div>
      <div className="review-grid">
        <Info label="Gender" value={profile.gender}/><Info label="Community" value={profile.community}/><Info label="Qualification" value={profile.education}/><Info label="Profession" value={profile.profession}/><Info label="Income" value={profile.income}/><Info label="Preferred Location" value={profile.preferred_location}/>
      </div>
    </section>
  </main>;
}
function Info({label,value}) { return <div className="review-item"><strong>{label}</strong><span>{value || "Not specified"}</span></div>; }
