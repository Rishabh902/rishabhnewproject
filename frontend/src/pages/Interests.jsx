import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";

function errorMessage(error, fallback = "Something went wrong") {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return detail?.message || fallback;
}

function Person({ item }) {
  const base = api.defaults.baseURL;
  const id = item.other_user_id || (item.sender_id === item.viewer_id ? item.receiver_id : item.sender_id);
  return <div className="person-mini">
    {item.other_user_photo_url ? <img src={`${base}${item.other_user_photo_url}`} alt="" /> : <div className="person-mini-empty">MS</div>}
    <div><strong>{item.other_user_name || "Member"}</strong><Link to={`/profile/${id}`}>View profile</Link></div>
  </div>;
}

export default function Interests() {
  const [sent, setSent] = useState([]);
  const [received, setReceived] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null);
  const [message, setMessage] = useState("");

  const load = async () => {
    setLoading(true); setMessage("");
    try {
      const [s, r] = await Promise.all([api.get("/api/interests/sent"), api.get("/api/interests/received")]);
      setSent(s.data); setReceived(r.data);
    } catch (e) { setMessage(errorMessage(e, "Unable to load interests")); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const action = async (id, type) => {
    setBusy(`${type}-${id}`); setMessage("");
    try {
      await api.post(`/api/interests/${id}/${type}`);
      await load();
    } catch (e) { setMessage(errorMessage(e)); }
    finally { setBusy(null); }
  };

  const withdraw = async (id) => {
    setBusy(`withdraw-${id}`); setMessage("");
    try { await api.delete(`/api/interests/${id}`); await load(); }
    catch (e) { setMessage(errorMessage(e)); }
    finally { setBusy(null); }
  };

  if (loading) return <main className="page"><div className="card"><h1>Interests</h1><p>Loading...</p></div></main>;

  return <main className="page wide">
    <div className="page-header"><div><h1>Interests</h1><p className="muted">Manage the profiles you are interested in and respond to incoming interests.</p></div><button onClick={load}>Refresh</button></div>
    {message && <div className="card"><p className="error">{message}</p></div>}

    <section className="card">
      <h2>Received</h2>
      {received.length === 0 ? <p className="muted">No interests received yet.</p> : received.map(item => <div className="list-row" key={item.id}>
        <Person item={item} />
        <span className={`status ${item.status.toLowerCase()}`}>{item.status}</span>
        {item.status === "PENDING" && <div className="row-actions"><button disabled={busy === `accept-${item.id}`} onClick={() => action(item.id, "accept")}>Accept</button><button className="secondary" disabled={busy === `reject-${item.id}`} onClick={() => action(item.id, "reject")}>Reject</button></div>}
      </div>)}
    </section>

    <section className="card">
      <h2>Sent</h2>
      {sent.length === 0 ? <p className="muted">You have not sent any interests.</p> : sent.map(item => <div className="list-row" key={item.id}>
        <Person item={item} />
        <span className={`status ${item.status.toLowerCase()}`}>{item.status}</span>
        {item.status === "PENDING" && <button className="secondary" disabled={busy === `withdraw-${item.id}`} onClick={() => withdraw(item.id)}>Withdraw</button>}
      </div>)}
    </section>
  </main>;
}
