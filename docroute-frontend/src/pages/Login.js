import { useState } from "react";
import { Container, Card, Form, Alert, Spinner } from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";
import { getErrorMessage } from "../utils/errorHandler";
import NavbarMenu from "../components/NavbarMenu";
import Orb from "../components/Orb";
import "../styles/Login.css";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  /* =========================
     HANDLE LOGIN
  ========================= */
  const handleLogin = async (e) => {
    e.preventDefault();

    if (loading) return; // prevent double submit

    setError("");

    const normalizedEmail = email.trim().toLowerCase();
    const trimmedPassword = password.trim();

    if (!normalizedEmail || !trimmedPassword) {
      setError("Email and password are required");
      return;
    }

    setLoading(true);

    try {
      const response = await api.post("/auth/login", {
        email: normalizedEmail,
        password: trimmedPassword,
      });

      const token = response?.data?.access_token;
      const user = response?.data?.user;

      if (!token) {
        throw new Error("Invalid server response");
      }

      // ✅ Store auth data
      localStorage.setItem("token", token);

      if (user) {
        localStorage.setItem("user", JSON.stringify(user));
      }

      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = email.trim() !== "" && password.trim() !== "";

  return (
    <div className="login-page">
      {/* 🔮 Orb Background */}
      <div className="login-orb-bg">
        <Orb
          backgroundColor="#000000"
          hoverIntensity={0.15}
          rotateOnHover
        />
      </div>

      {/* 🔝 Navbar */}
      <NavbarMenu />

      {/* 📦 Login Card */}
      <Container className="login-content d-flex justify-content-center align-items-center mt-5">
        <div className="card-container">
          <Card className="card-glass shadow-lg border-0">
            <Card.Body>
              <h3 className="text-center mb-3">
                Login to your account
              </h3>

              <p className="text-center text-muted">
                Enter your credentials to access your dashboard
              </p>

              {error && (
                <Alert
                  variant="danger"
                  dismissible
                  onClose={() => setError("")}
                >
                  {error}
                </Alert>
              )}

              <Form onSubmit={handleLogin} noValidate>
                <Form.Group className="mb-3">
                  <Form.Label>Email Address</Form.Label>
                  <Form.Control
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                    disabled={loading}
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Password</Form.Label>
                  <Form.Control
                    type="password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    disabled={loading}
                  />
                </Form.Group>

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
                    {loading ? "Logging in..." : "Login"}
                  </span>
                </button>

                {/* Links */}
                <div className="login-links">
                  <Link to="/forgot-password" className="link-primary">
                    Forgot your password?
                  </Link>

                  <div className="signup-text">
                    Don’t have an account?
                    <Link to="/register" className="link-primary ms-1">
                      Create an account
                    </Link>
                  </div>

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

export default Login;
