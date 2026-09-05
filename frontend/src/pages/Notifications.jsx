import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";

function timeText(value) { try { return new Date(value).toLocaleString(); } catch { return ""; } }

export default function Notifications() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const load = async () => {
    setLoading(true); setMessage("");
    try { const r = await api.get("/api/notifications"); setItems(r.data); }
    catch (e) { setMessage(e.response?.data?.detail || "Unable to load notifications"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const read = async (id) => {
    try { const r = await api.post(`/api/notifications/${id}/read`); setItems(v => v.map(x => x.id === id ? r.data : x)); }
    catch (e) { setMessage(e.response?.data?.detail || "Unable to update notification"); }
  };
  const remove = async (id) => {
    try { await api.delete(`/api/notifications/${id}`); setItems(v => v.filter(x => x.id !== id)); }
    catch (e) { setMessage(e.response?.data?.detail || "Unable to delete notification"); }
  };

  return <main className="page wide">
    <div className="page-header"><div><h1>Notifications</h1><p className="muted">Interest, match and account activity.</p></div><button onClick={load}>Refresh</button></div>
    {message && <div className="card"><p className="error">{message}</p></div>}
    {loading ? <div className="card"><p>Loading notifications...</p></div> : items.length === 0 ? <div className="card"><h2>No notifications</h2><p className="muted">You are all caught up.</p></div> : <div>
      {items.map(item => <article className={`card notification ${item.is_read ? "read" : "unread"}`} key={item.id}>
        <div className="notification-main"><span className="notification-dot"/><div><h3>{item.title}</h3><p>{item.message}</p><small className="muted">{timeText(item.created_at)}</small>{item.payload?.user_id && <p><Link to={`/profile/${item.payload.user_id}`}>Open profile</Link></p>}</div></div>
        <div className="row-actions">{!item.is_read && <button onClick={() => read(item.id)}>Mark read</button>}<button className="secondary" onClick={() => remove(item.id)}>Delete</button></div>
      </article>)}
    </div>}
  </main>;
}
