import { useState, useEffect } from "react";
import { Container, Card, Form, Alert, Spinner } from "react-bootstrap";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "../services/api";
import NavbarMenu from "../components/NavbarMenu";
import Orb from "../components/Orb";
import "../styles/Login.css";

function ResetPassword() {
  const { token } = useParams();
  const navigate = useNavigate();

  /* ================= STATE ================= */
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [passwordError, setPasswordError] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [loading, setLoading] = useState(false);
  const [tokenValid, setTokenValid] = useState(true);

  /* ================= TOKEN CHECK ================= */
  useEffect(() => {
    if (!token) {
      setTokenValid(false);
      setError("Invalid reset link");
    }
  }, [token]);

  /* ================= PASSWORD VALIDATION ================= */
  const validatePassword = (value) => {
    if (value.length < 8)
      return "Password must be at least 8 characters";

    if (!/[A-Z]/.test(value))
      return "Must include at least one uppercase letter";

    if (!/[0-9]/.test(value))
      return "Must include at least one number";

    if (!/[@$!%*?&]/.test(value))
      return "Must include at least one special character (@$!%*?&)";

    return "";
  };

  /* ================= SUBMIT ================= */
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;

    setError("");
    setMessage("");
    setPasswordError("");

    const trimmedPassword = password.trim();

    const validationMsg = validatePassword(trimmedPassword);
    if (validationMsg) {
      setPasswordError(validationMsg);
      return;
    }

    if (trimmedPassword !== confirmPassword.trim()) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);

    try {
      await api.post(`/auth/reset-password/${token}`, {
        new_password: trimmedPassword,
      });

      setMessage("Password reset successful. Redirecting...");

      setTimeout(() => {
        navigate("/login");
      }, 1500);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Invalid or expired reset link"
      );
    } finally {
      setLoading(false);
    }
  };

  /* ================= INVALID TOKEN VIEW ================= */
  if (!tokenValid) {
    return (
      <div className="login-page">
        <NavbarMenu />
        <Container className="mt-5 text-center">
          <Alert variant="danger">
            Invalid or missing reset token.
          </Alert>
          <Link to="/forgot-password">
            Request new reset link
          </Link>
        </Container>
      </div>
    );
  }

  /* ================= UI ================= */
  return (
    <div className="login-page">
      {/* Orb Background */}
      <div className="login-orb-bg">
        <Orb
          backgroundColor="#000000"
          hoverIntensity={0.15}
          rotateOnHover
        />
      </div>

      <NavbarMenu />

      <Container className="login-content d-flex justify-content-center align-items-center mt-5">
        <div className="card-container">
          <Card className="card-glass shadow-lg border-0">
            <Card.Body>
              <h3 className="text-center mb-3">
                Reset Password
              </h3>

              {error && (
                <Alert
                  variant="danger"
                  dismissible
                  onClose={() => setError("")}
                >
                  {error}
                </Alert>
              )}

              {message && (
                <Alert variant="success">
                  {message}
                </Alert>
              )}

              <Form onSubmit={handleSubmit} noValidate>
                {/* NEW PASSWORD */}
                <Form.Group className="mb-3">
                  <Form.Label>New Password</Form.Label>
                  <Form.Control
                    type="password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (passwordError)
                        setPasswordError("");
                    }}
                    isInvalid={!!passwordError}
                    required
                  />
                  <Form.Control.Feedback type="invalid">
                    {passwordError}
                  </Form.Control.Feedback>

                  <div className="text-muted small mt-1">
                    8+ characters, uppercase,
                    number & special character.
                  </div>
                </Form.Group>

                {/* CONFIRM PASSWORD */}
                <Form.Group className="mb-3">
                  <Form.Label>
                    Confirm Password
                  </Form.Label>
                  <Form.Control
                    type="password"
                    value={confirmPassword}
                    onChange={(e) =>
                      setConfirmPassword(
                        e.target.value
                      )
                    }
                    required
                  />
                </Form.Group>

                {/* SUBMIT */}
                <button
                  type="submit"
                  className="bubbles w-100"
                  disabled={loading}
                >
                  <span className="text">
                    {loading ? (
                      <>
                        <Spinner
                          size="sm"
                          className="me-2"
                        />
                        Resetting...
                      </>
                    ) : (
                      "Reset Password"
                    )}
                  </span>
                </button>

                {/* LINKS */}
                <div className="login-links">
                  <Link
                    to="/login"
                    className="link-primary"
                  >
                    ← Back to login
                  </Link>

                  <Link
                    to="/"
                    className="link-muted"
                  >
                    ← Back to home
                  </Link>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </div>
      </Container>
    </div>
  );
}

export default ResetPassword;
