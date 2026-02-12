import { useEffect, useState, useCallback } from "react";
import api from "../services/api";
import { getErrorMessage } from "../utils/errorHandler";
import {
  Container,
  Row,
  Col,
  Card,
  Button,
  Form,
  Alert,
  Spinner,
  Table,
  Badge,
} from "react-bootstrap";

/* ===============================
   🔐 PASSWORD VALIDATOR
=============================== */
const isStrongPassword = (value) => {
  if (value.length < 8 || value.length > 72) return false;
  if (!/[A-Z]/.test(value)) return false;
  if (!/[a-z]/.test(value)) return false;
  if (!/\d/.test(value)) return false;
  if (!/[!@#$%^&*()_+=\-{}[\]:;"'<>,.?/]/.test(value)) return false;
  return true;
};

export default function DocCodeExchange() {
  const [file, setFile] = useState(null);
  const [password, setPassword] = useState("");
  const [generatedCode, setGeneratedCode] = useState("");

  const [receiveCode, setReceiveCode] = useState("");
  const [receivePassword, setReceivePassword] = useState("");

  const [sentHistory, setSentHistory] = useState([]);
  const [receivedHistory, setReceivedHistory] = useState([]);

  const [loadingGenerate, setLoadingGenerate] = useState(false);
  const [loadingReceive, setLoadingReceive] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  /* ===============================
     📜 LOAD HISTORY (SAFE)
  =============================== */
  const loadHistory = useCallback(async (background = false) => {
    try {
      if (background) setRefreshing(true);

      const [sent, received] = await Promise.all([
        api.get("/doc-code/history/sent"),
        api.get("/doc-code/history/received"),
      ]);

      setSentHistory(sent?.data || []);
      setReceivedHistory(received?.data || []);
    } catch (err) {
      if (!background) setError(getErrorMessage(err));
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();

    const interval = setInterval(() => {
      loadHistory(true); // silent refresh
    }, 30000);

    return () => clearInterval(interval);
  }, [loadHistory]);

  /* ===============================
     📤 GENERATE CODE
  =============================== */
  const generateCode = async () => {
    if (!file) return setError("Select a file first");

    if (password && !isStrongPassword(password)) {
      return setError(
        "Password must be 8–72 chars with upper, lower, number & symbol"
      );
    }

    setLoadingGenerate(true);
    setError("");
    setMessage("");

    const form = new FormData();
    form.append("file", file);
    if (password) form.append("password", password);

    try {
      const res = await api.post("/doc-code/generate", form);

      setGeneratedCode(res?.data?.code || "");
      setMessage("Code generated successfully");

      setFile(null);
      setPassword("");
      await loadHistory(true);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoadingGenerate(false);
    }
  };

  /* ===============================
     📥 RECEIVE DOCUMENT
  =============================== */
  const receiveDocument = async () => {
    if (!receiveCode) return setError("Enter document code");

    setLoadingReceive(true);
    setError("");
    setMessage("");

    try {
      const res = await api.post(
        "/doc-code/receive",
        { code: receiveCode, password: receivePassword || undefined },
        { responseType: "blob" }
      );

      const blob = new Blob([res.data], {
        type: res.headers?.["content-type"] || "application/octet-stream",
      });

      let filename = "document";
      const disposition = res.headers?.["content-disposition"];
      if (disposition) {
        const match = disposition.match(/filename="?(.+)"?/i);
        if (match?.[1]) filename = match[1];
      }

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      setMessage("Document downloaded successfully");
      setReceiveCode("");
      setReceivePassword("");

      await loadHistory(true);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoadingReceive(false);
    }
  };

  /* ===============================
     🧠 HELPERS
  =============================== */
  const isExpired = (d) =>
    new Date(d?.expires_at) < new Date();

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(generatedCode);
      setMessage("Code copied to clipboard");
    } catch {
      setError("Clipboard access denied");
    }
  };

  const timeLeft = (date) => {
    const diff = new Date(date) - new Date();
    if (diff <= 0) return "Expired";
    const minutes = Math.floor(diff / 60000);
    return `${minutes} min left`;
  };

  /* ===============================
     UI
  =============================== */
  return (
    <Container className="mt-4">
      <h3 className="text-center mb-4">
        🔐 Secure Document Code Exchange {refreshing && "• Updating"}
      </h3>

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

      {/* SEND / RECEIVE */}
      <Row>
        <Col md={6}>
          <Card className="mb-4 shadow-sm">
            <Card.Header>📤 Upload & Generate</Card.Header>
            <Card.Body>
              <Form.Control
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />

              <Form.Control
                className="mt-2"
                type="password"
                placeholder="Optional password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />

              <Button
                className="mt-3 w-100"
                style={{ backgroundColor: "#5a83c1", borderColor: "#5a83c1" }}
                onClick={generateCode}
                disabled={loadingGenerate}
              >
                {loadingGenerate ? <Spinner size="sm" /> : "Generate Code"}
              </Button>

              {generatedCode && (
                <div className="mt-3 text-center">
                  <div className="fw-bold fs-5">{generatedCode}</div>
                  <Button
                    size="sm"
                    variant="outline-secondary"
                    className="mt-2"
                    onClick={copyCode}
                  >
                    Copy Code
                  </Button>
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>

        <Col md={6}>
          <Card className="mb-4 shadow-sm">
            <Card.Header>📥 Receive</Card.Header>
            <Card.Body>
              <Form.Control
                placeholder="Document Code"
                value={receiveCode}
                onChange={(e) =>
                  setReceiveCode(e.target.value.toUpperCase())
                }
              />

              <Form.Control
                className="mt-2"
                type="password"
                placeholder="Password (if required)"
                value={receivePassword}
                onChange={(e) => setReceivePassword(e.target.value)}
              />

              <Button
                className="mt-3 w-100"
                style={{ backgroundColor: "#5a83c1", borderColor: "#5a83c1" }}
                onClick={receiveDocument}
                disabled={loadingReceive}
              >
                {loadingReceive ? <Spinner size="sm" /> : "Receive Document"}
              </Button>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* HISTORY */}
      <Row>
        <Col md={6}>
          <Card className="shadow-sm">
            <Card.Header>📤 Sent History</Card.Header>
            <Card.Body style={{ maxHeight: 300, overflowY: "auto" }}>
              <Table bordered size="sm">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Status</th>
                    <th>Expiry</th>
                  </tr>
                </thead>
                <tbody>
                  {sentHistory?.length === 0 && (
                    <tr>
                      <td colSpan="3" className="text-center">
                        No records
                      </td>
                    </tr>
                  )}
                  {sentHistory?.map((d) => (
                    <tr key={d?.code}>
                      <td>{d?.code}</td>
                      <td>
                        {d?.is_used ? (
                          <Badge bg="success">Received</Badge>
                        ) : isExpired(d) ? (
                          <Badge bg="danger">Expired</Badge>
                        ) : (
                          <Badge bg="warning">Pending</Badge>
                        )}
                      </td>
                      <td>
                        {!isExpired(d) ? (
                          <Badge bg="info">
                            {timeLeft(d?.expires_at)}
                          </Badge>
                        ) : (
                          <Badge bg="secondary">Expired</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6}>
          <Card className="shadow-sm">
            <Card.Header>📥 Received History</Card.Header>
            <Card.Body style={{ maxHeight: 300, overflowY: "auto" }}>
              <Table bordered size="sm">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>File</th>
                    <th>From</th>
                  </tr>
                </thead>
                <tbody>
                  {receivedHistory?.length === 0 && (
                    <tr>
                      <td colSpan="3" className="text-center">
                        No records
                      </td>
                    </tr>
                  )}
                  {receivedHistory?.map((d) => (
                    <tr key={d?.code}>
                      <td>{d?.code}</td>
                      <td>{d?.file_name}</td>
                      <td>User #{d?.owner_user_id}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}
