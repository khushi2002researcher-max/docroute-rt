// src/services/api.js
import axios from "axios";

/* ==========================================
   BASE URL (ENV BASED - PRODUCTION READY)
========================================== */
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

/* ==========================================
   REQUEST INTERCEPTOR
   → Attach JWT Automatically
========================================== */
api.interceptors.request.use(
  (config) => {
    const token =
      localStorage.getItem("access_token") ||
      localStorage.getItem("token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

/* ==========================================
   RESPONSE INTERCEPTOR
   → Handle 401 (Auto Logout)
   → Handle Network Errors
   → Handle Server Errors
========================================== */
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // ===============================
    // 🔐 401 Unauthorized Handling
    // ===============================
    if (error.response?.status === 401) {
      // Prevent infinite redirect loops
      if (!originalRequest._retry) {
        originalRequest._retry = true;

        // If you implement refresh tokens later,
        // refresh logic will go here.
      }

      localStorage.removeItem("access_token");
      localStorage.removeItem("token");
      localStorage.removeItem("user");

      if (window.location.pathname !== "/login") {
        window.location.replace("/login");
      }
    }

    // ===============================
    // 🌐 Network Error Handling
    // ===============================
    if (!error.response) {
      console.error("Network error:", error.message);
    }

    // ===============================
    // 🚨 500 Server Errors
    // ===============================
    if (error.response?.status >= 500) {
      console.error("Server error:", error.response.data);
    }

    return Promise.reject(error);
  }
);

export default api;
