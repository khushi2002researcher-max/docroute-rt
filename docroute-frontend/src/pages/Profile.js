import { useState, useEffect, useMemo } from "react";
import { Card, Form, Button, Alert, Spinner } from "react-bootstrap";
import api from "../services/api";
import { useNavigate } from "react-router-dom";
import { getErrorMessage } from "../utils/errorHandler";
import "../styles/Profile.css";

/* ===============================
   DEFAULT AVATARS
================================ */
const defaultAvatars = [
  "/avatars/avatar-1.png",
  "/avatars/avatar-2.png",
  "/avatars/avatar-3.png",
  "/avatars/avatar-4.png",
  "/avatars/avatar-6.png",
  "/avatars/avatar-7.png",
  "/avatars/avatar-8.png",
];

/* ===============================
   PASSWORD VALIDATOR
================================ */
const validatePassword = (value) => {
  if (value.length < 8) return "Password must be at least 8 characters";
  if (!/[A-Z]/.test(value)) return "Must include uppercase letter";
  if (!/[0-9]/.test(value)) return "Must include a number";
  if (!/[@$!%*?&]/.test(value))
    return "Must include special character (@$!%*?&)";
  return "";
};

export default function Profile() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [avatarLoading, setAvatarLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const API_BASE =
    process.env.REACT_APP_API_URL || window.location.origin;

  /* =========================
     LOAD PROFILE
  ========================= */
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const res = await api.get("/auth/me");
        setUser(res?.data);

        if (res?.data?.avatar_url) {
          localStorage.setItem(
            "avatar",
            JSON.stringify({
              path: res.data.avatar_url,
              updatedAt: Date.now(),
            })
          );
        }
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };

    loadProfile();
  }, []);

  /* =========================
     SAFE AVATAR PARSE
  ========================= */
  const avatarMeta = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem("avatar")) || {};
    } catch {
      return {};
    }
  }, [user]);

  const avatarSrc = avatarMeta?.path
    ? avatarMeta.path.startsWith("/uploads/")
      ? `${API_BASE}${avatarMeta.path}?v=${avatarMeta.updatedAt}`
      : avatarMeta.path
    : "/default-avatar.png";

  /* =========================
     DELETE ACCOUNT
  ========================= */
  const handleDeleteAccount = async () => {
    const confirmed = window.confirm(
      "Are you sure?\nThis will permanently delete your account and ALL data."
    );
    if (!confirmed) return;

    try {
      await api.delete("/auth/delete-account");
      localStorage.clear();
      navigate("/login");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  /* =========================
     AVATAR UPLOAD
  ========================= */
  const uploadAvatar = async (file) => {
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Only image files allowed");
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      setError("Max file size is 2MB");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setAvatarLoading(true);
      setError("");

      const res = await api.put("/auth/avatar", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const avatarPath = res?.data?.avatar;

      setUser((prev) => ({
        ...prev,
        avatar_url: avatarPath,
      }));

      localStorage.setItem(
        "avatar",
        JSON.stringify({
          path: avatarPath,
          updatedAt: Date.now(),
        })
      );

      setMessage("Avatar updated successfully");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setAvatarLoading(false);
    }
  };

  /* =========================
     SELECT DEFAULT AVATAR
  ========================= */
  const selectPresetAvatar = async (src) => {
    try {
      setAvatarLoading(true);
      const response = await fetch(src);
      const blob = await response.blob();
      const file = new File([blob], "avatar.png", {
        type: "image/png",
      });
      await uploadAvatar(file);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setAvatarLoading(false);
    }
  };

  /* =========================
     CHANGE PASSWORD
  ========================= */
  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (passwordLoading) return;

    setPasswordError("");
    setError("");

    const validationMessage = validatePassword(newPassword);
    if (validationMessage) {
      setPasswordError(validationMessage);
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError("Passwords do not match");
      return;
    }

    try {
      setPasswordLoading(true);

      await api.put("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });

      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");

      setMessage("Password updated successfully");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setPasswordLoading(false);
    }
  };

  /* =========================
     UI STATES
  ========================= */
  if (loading) return <Spinner animation="border" />;

  return (
    <div style={{ maxWidth: 560, margin: "40px auto" }}>
      <h4 className="mb-4">My Account</h4>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      {message && (
        <Alert variant="success" dismissible onClose={() => setMessage("")}>
          {message}
        </Alert>
      )}

      {/* AVATAR */}
      <Card className="mb-4 text-center">
        <Card.Body>
          <img
            src={avatarSrc}
            alt="avatar"
            className="rounded-circle mb-3"
            style={{ width: 90, height: 90, objectFit: "cover" }}
          />

          <Form.Control
            type="file"
            accept="image/*"
            disabled={avatarLoading}
            onChange={(e) => uploadAvatar(e.target.files?.[0])}
          />

          <div className="text-muted mt-3 mb-2">
            Or choose an avatar
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "center" }}>
            {defaultAvatars.map((src) => (
              <img
                key={src}
                src={src}
                onClick={() => selectPresetAvatar(src)}
                alt="avatar"
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: "50%",
                  cursor: "pointer",
                  border: "2px solid #e5e7eb",
                  objectFit: "cover",
                }}
              />
            ))}
          </div>
        </Card.Body>
      </Card>

      {/* ACCOUNT INFO */}
      <Card className="mb-4 text-center">
        <Card.Body>
          <div className="fw-semibold">{user?.full_name}</div>
          <small className="text-muted">{user?.email}</small>
        </Card.Body>
      </Card>

      {/* PASSWORD */}
      <Card>
        <Card.Body>
          <h6 className="mb-3">Change Password</h6>

          <Form onSubmit={handleChangePassword}>
            <Form.Control
              type="password"
              placeholder="Current password"
              className="mb-2"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />

            <Form.Control
              type="password"
              placeholder="New password"
              className="mb-1"
              value={newPassword}
              onChange={(e) => {
                setNewPassword(e.target.value);
                if (passwordError) setPasswordError("");
              }}
              isInvalid={!!passwordError}
              required
            />

            {passwordError && (
              <div className="text-danger small mb-2">
                {passwordError}
              </div>
            )}

            <Form.Control
              type="password"
              placeholder="Confirm new password"
              className="mb-3"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />

            <Button
              type="submit"
              className="w-100"
              disabled={passwordLoading}
            >
              {passwordLoading ? <Spinner size="sm" /> : "Update Password"}
            </Button>
          </Form>
        </Card.Body>
      </Card>

      {/* DELETE */}
      <Card className="mt-4 border-danger">
        <Card.Body>
          <Button
            variant="danger"
            className="w-100"
            onClick={handleDeleteAccount}
          >
            Delete Account Permanently
          </Button>
        </Card.Body>
      </Card>
    </div>
  );
}
