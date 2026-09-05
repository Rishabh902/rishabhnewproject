import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";

export default function Shortlist() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(null);
  const base = api.defaults.baseURL;

  const load = async () => {
    setLoading(true); setMessage("");
    try { const r = await api.get("/api/shortlists"); setItems(r.data); }
    catch (e) { setMessage(e.response?.data?.detail || "Unable to load shortlist"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const remove = async (id) => {
    setBusy(id); setMessage("");
    try { await api.delete(`/api/shortlists/${id}`); setItems(v => v.filter(x => x.profile_user_id !== id)); }
    catch (e) { setMessage(e.response?.data?.detail || "Unable to remove profile"); }
    finally { setBusy(null); }
  };

  return <main className="page wide">
    <div className="page-header"><div><h1>Shortlist</h1><p className="muted">Profiles you want to revisit later.</p></div><button onClick={load}>Refresh</button></div>
    {message && <div className="card"><p className="error">{message}</p></div>}
    {loading ? <div className="card"><p>Loading shortlist...</p></div> : items.length === 0 ? <div className="card"><h2>Your shortlist is empty</h2><p className="muted">Open a profile from Matches and choose Add to Shortlist.</p><Link className="button" to="/matches">Browse Matches</Link></div> : <div className="match-grid">
      {items.map(item => <article className="card match-card" key={item.id}>
        {item.profile_photo_url ? <img src={`${base}${item.profile_photo_url}`} alt={item.profile_name || "Profile"} /> : <div className="match-photo-empty">No photo</div>}
        <div className="match-card-body"><h3>{item.profile_name || "Member"}</h3><p className="muted">Shortlisted profile</p><Link className="button" to={`/profile/${item.profile_user_id}`}>View Profile</Link><button className="secondary" disabled={busy === item.profile_user_id} onClick={() => remove(item.profile_user_id)}>Remove</button></div>
      </article>)}
    </div>}
  </main>;
}
