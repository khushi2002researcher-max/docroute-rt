import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import api from "../services/api"; // ✅ REQUIRED
import "./Sidebar.css";

function Sidebar() {
  const navigate = useNavigate();

  const getAvatarFromStorage = () => {
    const raw = localStorage.getItem("avatar");
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  };

  const [avatar, setAvatar] = useState(getAvatarFromStorage());

  useEffect(() => {
    const refreshAvatar = () => {
      setAvatar(getAvatarFromStorage());
    };

    window.addEventListener("avatar-updated", refreshAvatar);
    return () =>
      window.removeEventListener("avatar-updated", refreshAvatar);
  }, []);

 const handleLogout = async () => {
  try {
    await api.post("/auth/logout");
  } catch {}

  localStorage.removeItem("token");

  // DO NOT remove avatar
  window.dispatchEvent(new Event("avatar-updated"));

  navigate("/login");
};


  return (
    <div className="sidebar">
      <div className="sidebar-profile">
        <img
          src={
            avatar
              ? `http://localhost:8000${avatar.path}?v=${avatar.updatedAt}`
              : "/default-avatar.png"
          }
          alt="avatar"
          className="sidebar-avatar"
        />

        <Link to="/dashboard/profile" className="sidebar-profile-link">
          My Profile
        </Link>
      </div>

      <hr />

      <Link to="/dashboard/analytics">📂 Dashboard</Link>
      <Link to="/dashboard/ocr">📄 OCR Digitization</Link>
      <Link to="/dashboard/ai-summary">🤖 AI Summary & Tagging</Link>
      <Link to="/dashboard/tracking">🆔 Document Tracking</Link>
      <Link to="/dashboard/qr">📎 QR Document Tracking</Link>
      <Link to="/dashboard/aiworkflow">🔄 AI Workflow</Link>
      <Link to="/dashboard/doc-code">🔐 Doc Code Exchange</Link>

      <button
        className="sidebar-logout"
        onClick={handleLogout}
      >
        Logout
      </button>
    </div>
  );
}

export default Sidebar;
