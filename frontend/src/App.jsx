import { Navigate, Link, NavLink, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import CompleteProfile from "./pages/CompleteProfile";
import Verification from "./pages/Verification";
import AdminDashboard from "./pages/AdminDashboard";
import AdminProfileReview from "./pages/AdminProfileReview";
import AdminPayments from "./pages/AdminPayments";
import Matches from "./pages/Matches";
import ProfileView from "./pages/ProfileView";
import Interests from "./pages/Interests";
import Shortlist from "./pages/Shortlist";
import Notifications from "./pages/Notifications";
import Chat from "./pages/Chat";
import Subscription from "./pages/Subscription";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import "./styles.css";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <main className="page"><p>Loading...</p></main>;
  return user ? children : <Navigate to="/login" replace />;
}

function AdminProtected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <main className="page"><p>Loading...</p></main>;
  if (!user) return <Navigate to="/login" replace />;
  return user.role === "admin" ? children : <Navigate to="/dashboard" replace />;
}

function Sidebar() {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "admin";
  const identity = user?.phone || user?.email || "Member";

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">Matrimony Platform</div>
      <nav className="sidebar-nav">
        {isAdmin ? (
          <>
            <NavLink to="/admin" end>Profile Review</NavLink>
            <NavLink to="/admin/payments">Payments</NavLink>
          </>
        ) : (
          <>
            <NavLink to="/dashboard">Dashboard</NavLink>
            <NavLink to="/matches">AI Matches</NavLink>
            <NavLink to="/interests">Interests</NavLink>
            <NavLink to="/shortlist">Shortlist</NavLink>
            <NavLink to="/chat">Chat</NavLink>
            <NavLink to="/notifications">Notifications</NavLink>
            <NavLink to="/subscription">Subscription</NavLink>
            <NavLink to="/complete-profile">My Profile</NavLink>
            <NavLink to="/verification">Verification</NavLink>
          </>
        )}
      </nav>
      <div className="sidebar-user">
        <strong>{identity}</strong>
        <span>{isAdmin ? "Administrator" : "Member"}</span>
        <button type="button" onClick={logout}>Log out</button>
      </div>
    </aside>
  );
}

function AppShell({ children }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="shell-main">{children}</div>
    </div>
  );
}

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return <main className="page"><p>Loading...</p></main>;
  }

  if (user) {
    return (
      <AppShell>
        <Routes>
          <Route path="/" element={<Navigate to={user.role === "admin" ? "/admin" : "/dashboard"} replace />} />
          <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
          <Route path="/complete-profile" element={<Protected><CompleteProfile /></Protected>} />
          <Route path="/matches" element={<Protected><Matches /></Protected>} />
          <Route path="/interests" element={<Protected><Interests /></Protected>} />
          <Route path="/shortlist" element={<Protected><Shortlist /></Protected>} />
          <Route path="/chat" element={<Protected><Chat /></Protected>} />
          <Route path="/chat/:matchId" element={<Protected><Chat /></Protected>} />
          <Route path="/notifications" element={<Protected><Notifications /></Protected>} />
          <Route path="/subscription" element={<Protected><Subscription /></Protected>} />
          <Route path="/verification" element={<Protected><Verification /></Protected>} />
          <Route path="/profile/:userId" element={<Protected><ProfileView /></Protected>} />
          <Route path="/admin" element={<AdminProtected><AdminDashboard /></AdminProtected>} />
          <Route path="/admin/payments" element={<AdminProtected><AdminPayments /></AdminProtected>} />
          <Route path="/admin/profiles/:userId" element={<AdminProtected><AdminProfileReview /></AdminProtected>} />
          <Route path="*" element={<Navigate to={user.role === "admin" ? "/admin" : "/dashboard"} replace />} />
        </Routes>
      </AppShell>
    );
  }

  return (
    <>
      <nav>
        <Link to="/">Matrimony Platform</Link>
        <span><Link to="/register">Register</Link><Link to="/login">Login</Link></span>
      </nav>
      <Routes>
        <Route
          path="/"
          element={
            <main className="hero">
              <h1>Matrimony Platform</h1>
              <p>Register &rarr; create profile &rarr; verify OTP &rarr; complete profile &rarr; admin approval &rarr; AI matching &rarr; interests &rarr; chat &rarr; subscription.</p>
              <Link className="button" to="/register">Get Started</Link>
            </main>
          }
        />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </>
  );
}
