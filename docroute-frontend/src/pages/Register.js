import { useState } from "react";
import { Container, Card, Form, Alert, Spinner } from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";              // ✅ centralized axios
import { getErrorMessage } from "../utils/errorHandler"; // optional if you created it
import NavbarMenu from "../components/NavbarMenu";
import Orb from "../components/Orb";
import "../styles/Login.css";

function Register() {
  const navigate = useNavigate();

  /* ================= STATE ================= */
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [agree, setAgree] = useState(false);

  const [loading, setLoading] = useState(false);

  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");

  /* ================= VALIDATION ================= */

  const validateEmail = (value) => {
    const trimmed = value.trim().toLowerCase();

    if (!trimmed.includes("@")) {
      return "Email must include @ symbol";
    }

    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!regex.test(trimmed)) {
      return "Enter a valid email address";
    }

    return "";
  };

  const validatePassword = (value) => {
    const regex =
      /^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$/;

    if (!regex.test(value)) {
      return "Password must be at least 8 characters, include uppercase, number & special character";
    }

    return "";
  };

  const capitalizeName = (value) =>
    value
      .toLowerCase()
      .replace(/\b\w/g, (char) => char.toUpperCase());

  /* ================= SUBMIT ================= */

  const handleRegister = async (e) => {
    e.preventDefault();
    if (loading) return;

    setError("");
    setSuccess("");
    setEmailError("");
    setPasswordError("");

    const trimmedEmail = email.trim().toLowerCase();
    const trimmedName = fullName.trim();

    // Email validation
    const emailMsg = validateEmail(trimmedEmail);
    if (emailMsg) {
      setEmailError(emailMsg);
      return;
    }

    // Password validation
    const passwordMsg = validatePassword(password);
    if (passwordMsg) {
      setPasswordError(passwordMsg);
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (!agree) {
      setError("You must agree to Terms and Conditions");
      return;
    }

    setLoading(true);

    try {
      await api.post("/auth/register", {
        full_name: trimmedName,
        email: trimmedEmail,
        password,
      });

      setSuccess("Registration successful! Redirecting...");

      setTimeout(() => {
        navigate("/login");
      }, 1500);
    } catch (err) {
      setError(
        getErrorMessage
          ? getErrorMessage(err)
          : err.response?.data?.detail || "Registration failed"
      );
    } finally {
      setLoading(false);
    }
  };

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
                Create your account
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

              {success && (
                <Alert variant="success">
                  {success}
                </Alert>
              )}

              <Form onSubmit={handleRegister} noValidate>
                {/* FULL NAME */}
                <Form.Group className="mb-3">
                  <Form.Label>Full Name</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Enter full name"
                    value={fullName}
                    onChange={(e) =>
                      setFullName(
                        capitalizeName(e.target.value)
                      )
                    }
                    required
                  />
                </Form.Group>

                {/* EMAIL */}
                <Form.Group className="mb-3">
                  <Form.Label>Email</Form.Label>
                  <Form.Control
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (emailError) setEmailError("");
                    }}
                    isInvalid={!!emailError}
                    required
                  />
                  <Form.Control.Feedback type="invalid">
                    {emailError}
                  </Form.Control.Feedback>
                </Form.Group>

                {/* PASSWORD */}
                <Form.Group className="mb-3">
                  <Form.Label>Password</Form.Label>
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
                    8+ characters, include uppercase,
                    number & special character.
                  </div>
                </Form.Group>

                {/* CONFIRM PASSWORD */}
                <Form.Group className="mb-3">
                  <Form.Label>Confirm Password</Form.Label>
                  <Form.Control
                    type="password"
                    value={confirmPassword}
                    onChange={(e) =>
                      setConfirmPassword(e.target.value)
                    }
                    required
                  />
                </Form.Group>

                {/* TERMS */}
                <Form.Group className="mb-3">
                  <Form.Check
                    type="checkbox"
                    label="I agree to Terms & Privacy Policy"
                    checked={agree}
                    onChange={(e) =>
                      setAgree(e.target.checked)
                    }
                  />
                </Form.Group>

                {/* SUBMIT BUTTON */}
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
                        Creating...
                      </>
                    ) : (
                      "Create Account"
                    )}
                  </span>
                </button>

                {/* LINKS */}
                <div className="login-links">
                  <Link to="/login" className="link-primary">
                    Already have an account? Login
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

export default Register;
