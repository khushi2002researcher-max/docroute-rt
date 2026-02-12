import { useState } from "react";
import { Container, Card, Form, Alert, Spinner } from "react-bootstrap";
import { Link } from "react-router-dom";
import api from "../services/api";
import { getErrorMessage } from "../utils/errorHandler";
import NavbarMenu from "../components/NavbarMenu";
import Orb from "../components/Orb";
import "../styles/Login.css";

function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  /* =========================
     EMAIL VALIDATION
  ========================= */
  const validateEmail = (value) => {
    const trimmed = value.trim();

    if (!trimmed) return "Email is required";

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmed))
      return "Enter a valid email address";

    return "";
  };

  /* =========================
     HANDLE SUBMIT
  ========================= */
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (loading) return; // prevent double submit

    setMessage("");
    setError("");

    const normalizedEmail = email.trim().toLowerCase();
    const validationError = validateEmail(normalizedEmail);

    if (validationError) {
      setEmailError(validationError);
      return;
    }

    setEmailError("");
    setLoading(true);

    try {
      await api.post("/auth/forgot-password", {
        email: normalizedEmail,
      });

      setMessage(
        "If this email exists in our system, a reset link has been sent."
      );

      setEmail("");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = email.trim() !== "" && !validateEmail(email);

  return (
    <div className="login-page">
      {/* 🔮 Background Orb */}
      <div className="login-orb-bg">
        <Orb backgroundColor="#000000" hoverIntensity={0.15} rotateOnHover />
      </div>

      {/* 🔝 Navbar */}
      <NavbarMenu />

      {/* 📦 Card */}
      <Container className="login-content d-flex justify-content-center align-items-center mt-5">
        <div className="card-container">
          <Card className="card-glass shadow-lg border-0">
            <Card.Body>
              <h3 className="text-center mb-3">Forgot Password</h3>

              <p className="text-center text-muted">
                Enter your registered email address and we’ll send you a reset
                link.
              </p>

              {message && (
                <Alert
                  variant="success"
                  className="text-center"
                  dismissible
                  onClose={() => setMessage("")}
                >
                  {message}
                </Alert>
              )}

              {error && (
                <Alert
                  variant="danger"
                  className="text-center"
                  dismissible
                  onClose={() => setError("")}
                >
                  {error}
                </Alert>
              )}

              <Form onSubmit={handleSubmit} noValidate>
                <Form.Group className="mb-3">
                  <Form.Label>Email Address</Form.Label>
                  <Form.Control
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (emailError) setEmailError("");
                    }}
                    isInvalid={!!emailError}
                    disabled={loading}
                    autoComplete="email"
                  />
                  <Form.Control.Feedback type="invalid">
                    {emailError}
                  </Form.Control.Feedback>
                </Form.Group>

                {/* 🔵 Animated Bubble Button */}
                <button
                  type="submit"
                  className="bubbles w-100"
                  disabled={loading || !isFormValid}
                >
                  <span className="text d-flex justify-content-center align-items-center gap-2">
                    {loading && (
                      <Spinner
                        animation="border"
                        size="sm"
                        role="status"
                      />
                    )}
                    {loading ? "Sending..." : "Send Reset Link"}
                  </span>
                </button>

                {/* 🔗 Navigation Links */}
                <div className="login-links mt-3 d-flex justify-content-between">
                  <Link to="/login" className="link-primary">
                    ← Back to login
                  </Link>

                  <Link to="/" className="link-muted">
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

export default ForgotPassword;
