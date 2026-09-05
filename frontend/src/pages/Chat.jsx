import { useEffect, useRef, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import api from "../api/client";

function errorMessage(error, fallback = "Something went wrong") {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return detail?.message || fallback;
}

function timeText(value) {
  try { return new Date(value).toLocaleString(); } catch { return ""; }
}

export default function Chat() {
  const { matchId } = useParams();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const base = api.defaults.baseURL;
  const bottomRef = useRef(null);

  const active = conversations.find((c) => String(c.id) === String(matchId));

  const loadConversations = async () => {
    try {
      const r = await api.get("/api/chat/conversations");
      setConversations(r.data);
      return r.data;
    } catch (err) {
      setMessage(errorMessage(err, "Unable to load conversations"));
      return [];
    }
  };

  const loadMessages = async (id) => {
    try {
      const r = await api.get(`/api/chat/conversations/${id}/messages`);
      setMessages(r.data);
      await api.post(`/api/chat/conversations/${id}/read`);
    } catch (err) {
      setMessage(errorMessage(err, "Unable to load messages"));
    }
  };

  useEffect(() => {
    setLoading(true);
    loadConversations().then((list) => {
      if (!matchId && list.length > 0) {
        navigate(`/chat/${list[0].id}`, { replace: true });
      }
      setLoading(false);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (matchId) loadMessages(matchId);
  }, [matchId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (e) => {
    e.preventDefault();
    if (!draft.trim() || !matchId) return;
    setBusy(true);
    try {
      await api.post(`/api/chat/conversations/${matchId}/messages`, { content: draft.trim() });
      setDraft("");
      await loadMessages(matchId);
      await loadConversations();
    } catch (err) {
      setMessage(errorMessage(err, "Unable to send message"));
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <main className="page wide"><div className="card"><p>Loading conversations...</p></div></main>;

  return (
    <main className="page wide">
      <div className="page-header">
        <div><h1>Chat</h1><p className="muted">Chat opens automatically once an interest is accepted on both sides.</p></div>
      </div>
      {message && <div className="card"><p className="error">{message}</p></div>}

      {conversations.length === 0 ? (
        <div className="card">
          <h2>No conversations yet</h2>
          <p className="muted">Accept an interest from a match to start chatting.</p>
          <Link className="button" to="/interests">Go to Interests</Link>
        </div>
      ) : (
        <div className="chat-shell">
          <aside className="chat-list">
            {conversations.map((c) => (
              <button
                key={c.id}
                className={`chat-list-item ${String(c.id) === String(matchId) ? "active" : ""}`}
                onClick={() => navigate(`/chat/${c.id}`)}
              >
                {c.other_user_photo_url ? (
                  <img src={`${base}${c.other_user_photo_url}`} alt="" />
                ) : (
                  <div className="person-mini-empty">MS</div>
                )}
                <div className="chat-list-meta">
                  <strong>{c.other_user_name || "Member"}</strong>
                  <span className="muted">{c.last_message || "Say hello!"}</span>
                </div>
                {c.unread_count > 0 && <span className="chat-unread-badge">{c.unread_count}</span>}
              </button>
            ))}
          </aside>

          <section className="chat-panel card">
            {!active ? (
              <p className="muted">Select a conversation.</p>
            ) : (
              <>
                <div className="chat-panel-header">
                  <strong>{active.other_user_name || "Member"}</strong>
                  <Link to={`/profile/${active.other_user_id}`}>View profile</Link>
                </div>
                <div className="chat-messages">
                  {messages.length === 0 && <p className="muted">No messages yet. Say hello!</p>}
                  {messages.map((m) => (
                    <div key={m.id} className={`chat-bubble ${m.sender_id === active.other_user_id ? "theirs" : "mine"}`}>
                      <p>{m.content}</p>
                      <span>{timeText(m.created_at)}</span>
                    </div>
                  ))}
                  <div ref={bottomRef} />
                </div>
                <form className="chat-composer" onSubmit={send}>
                  <input
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    placeholder="Type a message..."
                    maxLength={2000}
                  />
                  <button disabled={busy || !draft.trim()}>Send</button>
                </form>
              </>
            )}
          </section>
        </div>
      )}
    </main>
  );
}
