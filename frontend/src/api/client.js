import axios from "axios";

export const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const mediaUrl = (url) => {
  if (!url) return "";
  return url.startsWith("http://") || url.startsWith("https://") ? url : `${API_BASE}${url}`;
};

const api = axios.create({ baseURL: API_BASE });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
export default api;
