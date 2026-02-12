import api from "../services/api";

export const logoutUser = async (navigate) => {
  try {
    await api.post("/auth/logout");
  } catch {
    // ignore errors (token may already be invalid)
  }

  // clear local storage
  localStorage.removeItem("token");
  localStorage.removeItem("avatar");

  // notify sidebar
  window.dispatchEvent(new Event("avatar-updated"));

  // redirect
  navigate("/login");
};
