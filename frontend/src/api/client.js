import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "/api/v1";

const client = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("sis_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    // Only redirect to login if the FAILED request was NOT the login endpoint itself
    // and the user has no token stored (truly unauthenticated).
    // Do NOT redirect on 401s from optional dashboard data fetches.
    if (err.response?.status === 401) {
      const url = err.config?.url || "";
      const isLoginRequest = url.includes("/auth/login");
      const hasToken = !!localStorage.getItem("sis_token");

      // If there's no token at all, kick to login
      if (!hasToken && !isLoginRequest) {
        window.location.href = "/login";
      }
      // Otherwise just reject the promise — let the component handle it gracefully
    }
    return Promise.reject(err);
  }
);

export default client;
