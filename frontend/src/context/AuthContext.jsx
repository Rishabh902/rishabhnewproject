import { createContext, useContext, useEffect, useState } from "react";
import api from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api.get("/api/auth/me")
      .then((r) => setUser(r.data))
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      })
      .finally(() => setLoading(false));
  }, []);

  const saveSession = async (data) => {
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const me = await api.get("/api/auth/me");
    setUser(me.data);
    return me.data;
  };

  const loginWithPassword = async (contact, password) => {
    const { data } = await api.post("/api/auth/login", { contact, password });
    return saveSession(data);
  };

  const requestLoginOtp = async (contact) => {
    const { data } = await api.post("/api/auth/login/otp/request", { contact });
    return data;
  };

  const loginWithOtp = async (contact, otp) => {
    const { data } = await api.post("/api/auth/login/otp/verify", { contact, otp });
    return saveSession(data);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      loginWithPassword,
      requestLoginOtp,
      loginWithOtp,
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
