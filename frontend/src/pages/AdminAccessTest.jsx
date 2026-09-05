import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";

export default function AdminAccessTest() {
  const [state, setState] = useState({ loading: true, data: null, error: null });

  useEffect(() => {
    let mounted = true;

    api.get("/api/admin/access-test")
      .then((response) => {
        if (mounted) {
          setState({ loading: false, data: response.data, error: null });
        }
      })
      .catch((error) => {
        if (mounted) {
          setState({
            loading: false,
            data: null,
            error: error.response?.data?.detail || "Unable to access admin API",
          });
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  if (state.loading) {
    return <main className="card"><h1>Admin Access Test</h1><p>Testing admin authorization...</p></main>;
  }

  if (state.error) {
    return (
      <main className="card">
        <h1>Admin Access Test</h1>
        <p>{state.error}</p>
        <Link to="/dashboard">Back to Dashboard</Link>
      </main>
    );
  }

  return (
    <main className="card">
      <h1>Admin Access Test</h1>
      <p>{state.data.message}</p>
      <pre>{JSON.stringify(state.data.admin, null, 2)}</pre>
      <Link to="/dashboard">Back to Dashboard</Link>
    </main>
  );
}
