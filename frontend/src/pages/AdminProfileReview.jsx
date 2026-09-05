import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../api/client";

function errorMessage(error, fallback) {
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message) return detail.message;
  return fallback;
}

export default function AdminProfileReview() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [reason, setReason] = useState("");
  const [showReject, setShowReject] = useState(false);

  const loadProfile = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get(`/api/admin/profiles/${userId}`);
      setProfile(response.data);
    } catch (err) {
      setError(errorMessage(err, "Unable to load profile"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, [userId]);

  const approve = async () => {
    if (!window.confirm("Approve this profile? It will become ACTIVE.")) return;

    setSaving(true);
    setError("");
    try {
      const response = await api.post(`/api/admin/profiles/${userId}/approve`);
      setProfile(response.data);
      window.alert("Profile approved successfully.");
      navigate("/admin");
    } catch (err) {
      setError(errorMessage(err, "Unable to approve profile"));
    } finally {
      setSaving(false);
    }
  };

  const reject = async (event) => {
    event.preventDefault();
    if (reason.trim().length < 3) {
      setError("Please enter a rejection reason.");
      return;
    }

    setSaving(true);
    setError("");
    try {
      const response = await api.post(`/api/admin/profiles/${userId}/reject`, {
        reason: reason.trim(),
      });
      setProfile(response.data);
      setShowReject(false);
      window.alert("Profile rejected and returned to DRAFT.");
      navigate("/admin");
    } catch (err) {
      setError(errorMessage(err, "Unable to reject profile"));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <main className="page"><div className="card"><h1>Profile Review</h1><p>Loading profile...</p></div></main>;
  }

  if (error && !profile) {
    return <main className="page"><div className="card"><h1>Profile Review</h1><p className="message">{error}</p><Link to="/admin">Back to Admin Dashboard</Link></div></main>;
  }

  return (
    <main className="page wide">
      <div className="page-header">
        <div>
          <h1>Profile Review</h1>
          <p>Review all submitted profile information before approval.</p>
        </div>
        <span className={`status ${profile.status.toLowerCase()}`}>{profile.status}</span>
      </div>

      {error && <div className="card"><p className="message">{error}</p></div>}

      <div className="card review-photo-card">
        {profile.photo_url ? (
          <img
            className="review-photo"
            src={`${api.defaults.baseURL}${profile.photo_url}`}
            alt={profile.name || "Profile"}
          />
        ) : (
          <div className="review-photo review-photo-empty">No photo uploaded</div>
        )}
      </div>

      <div className="card">
        <h2>Personal Information</h2>
        <div className="review-grid">
          <Info label="Name" value={profile.name} />
          <Info label="Gender" value={profile.gender} />
          <Info label="Date of Birth" value={profile.date_of_birth} />
          <Info label="Gothra" value={profile.gothra} />
          <Info label="Community" value={profile.community} />
          <Info label="Education" value={profile.education} />
          <Info label="Profession" value={profile.profession} />
          <Info label="Income" value={profile.income} />
          <Info label="Height" value={profile.height_cm ? `${profile.height_cm} cm` : null} />
          <Info label="Preferred Location" value={profile.preferred_location} />
          <Info label="Permanent Address" value={profile.permanent_address} full />
          <Info label="Family Details" value={profile.family_details} full />
        </div>
      </div>

      {profile.rejection_reason && (
        <div className="card">
          <h2>Previous Rejection Reason</h2>
          <p>{profile.rejection_reason}</p>
        </div>
      )}

      {profile.status === "PENDING_REVIEW" && (
        <div className="card review-actions">
          <h2>Admin Decision</h2>
          <p className="muted">Approve to make this profile ACTIVE, or reject it and return it to DRAFT.</p>
          <button onClick={approve} disabled={saving}>Approve Profile</button>
          <button className="secondary" onClick={() => setShowReject(true)} disabled={saving}>Reject Profile</button>
        </div>
      )}

      <p><Link to="/admin">← Back to Admin Dashboard</Link></p>

      {showReject && (
        <div className="modal-backdrop">
          <div className="modal card">
            <h2>Reject Profile</h2>
            <p>Enter the reason the user should correct before resubmitting.</p>
            <form onSubmit={reject}>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Example: Please upload a clearer profile photo."
                maxLength={2000}
                required
              />
              <div className="modal-actions">
                <button type="button" className="secondary" onClick={() => setShowReject(false)} disabled={saving}>
                  Cancel
                </button>
                <button type="submit" disabled={saving}>
                  {saving ? "Rejecting..." : "Confirm Rejection"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}

function Info({ label, value, full }) {
  return (
    <div className={full ? "review-item full" : "review-item"}>
      <strong>{label}</strong>
      <span>{value || "Not provided"}</span>
    </div>
  );
}
