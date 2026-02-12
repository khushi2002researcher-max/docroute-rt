import api from "../services/api";
import { getErrorMessage } from "../utils/errorHandler";
import {
  Card,
  Button,
  Form,
  Table,
  Modal,
  Badge,
  Spinner,
  Alert,
} from "react-bootstrap";
import { QRCodeCanvas } from "qrcode.react";
import { useEffect, useState, useRef } from "react";

/* ================= SAFE DATE ================= */
const formatDate = (v) => {
  if (!v) return "—";
  const d = new Date(v);
  return isNaN(d.getTime()) ? "—" : d.toLocaleString();
};

export default function QRPhysicalTracking() {
  const API_BASE =
    process.env.REACT_APP_API_URL || window.location.origin;

  /* ================= GLOBAL MESSAGES ================= */
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  /* ================= OWNER FORM ================= */
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [contact, setContact] = useState("");
  const [fileName, setFileName] = useState("");
  const [pdf, setPdf] = useState(null);
  const [restricted, setRestricted] = useState(false);
  const [ownerPassword, setOwnerPassword] = useState("");
  const [loading, setLoading] = useState(false);

  /* ================= DATA ================= */
  const [tracking, setTracking] = useState(null);
  const [history, setHistory] = useState([]);

  /* ================= QR ================= */
  const [qrModal, setQrModal] = useState(false);
  const [qrScans, setQrScans] = useState([]);
  const [qrToken, setQrToken] = useState(null);
  const [selectedDoc, setSelectedDoc] = useState(null);

  /* ================= PDF ================= */
  const [previewUrl, setPreviewUrl] = useState(null);

  const qrPrintRef = useRef(null);

  const shareUrl = qrToken
    ? `${window.location.origin}/share/physical/${qrToken}`
    : null;

  /* ================= PASSWORD VALIDATION ================= */
  const isValidPassword = (password) =>
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$/.test(password);

  /* ================= LOAD HISTORY ================= */
  const loadHistory = async () => {
    try {
      const res = await api.get("/qr/documents");
      setHistory(res?.data || []);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  /* ================= CREATE TRACKING ================= */
  const generateTracking = async () => {
    if (loading) return;

    if (!name.trim()) return setError("Owner name required");
    if (!/^\d{10}$/.test(contact))
      return setError("Contact must be exactly 10 digits");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
      return setError("Enter valid email");
    if (!pdf) return setError("PDF required");
    if (!isValidPassword(ownerPassword))
      return setError(
        "Password must be 8+ chars with uppercase, lowercase, number & special char"
      );

    setError("");
    setMessage("");
    setLoading(true);

    const fd = new FormData();
    fd.append("owner_name", name);
    fd.append("owner_email", email);
    fd.append("owner_contact", contact);
    fd.append("file_name", fileName);
    fd.append("owner_password", ownerPassword);
    fd.append("restrict_public_view", restricted ? "1" : "0");
    fd.append("file", pdf);

    try {
      const res = await api.post("/qr/create", fd);
      setTracking(res.data);
      setMessage("Tracking ID generated successfully");
      await loadHistory();

      setName("");
      setEmail("");
      setContact("");
      setFileName("");
      setPdf(null);
      setOwnerPassword("");
      setRestricted(false);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  /* ================= DELETE ================= */
  const deleteDocument = async (row) => {
    if (!window.confirm("Delete this tracking ID?")) return;
    try {
      await api.delete(`/qr/delete/${row?.id}`);
      setMessage("Deleted successfully");
      await loadHistory();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  /* ================= VIEW PDF ================= */
  const openView = (row) => {
    if (!row?.id) return;
    setPreviewUrl(`${API_BASE}/qr/preview/${row.id}`);
  };

  /* ================= QR ================= */
  const openQR = async (row) => {
    try {
      let activeQR = row?.active_qr;

      if (!activeQR) {
        const res = await api.post(`/qr/generate/${row.id}`);
        activeQR = { token: res.data.token };
        await loadHistory();
      }

      const scans = await api.get(`/qr/history/${row.id}`);

      setSelectedDoc(row);
      setQrScans(scans?.data || []);
      setQrToken(activeQR.token);
      setQrModal(true);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const revokeQR = async () => {
    if (!qrToken) return;
    if (!window.confirm("Revoke this QR?")) return;

    try {
      await api.post(`/qr/revoke/${qrToken}`);
      setMessage("QR revoked");
      setQrModal(false);
      setQrToken(null);
      await loadHistory();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const printQR = () => {
    const canvas = qrPrintRef.current?.querySelector("canvas");
    if (!canvas) return;

    const img = canvas.toDataURL("image/png");
    const win = window.open("", "", "width=600,height=800");
    win.document.write(`
      <html>
      <body style="text-align:center;padding:40px;">
      <img src="${img}" width="220"/>
      <div style="margin-top:15px;font-weight:bold;">
      Tracking ID: ${selectedDoc?.tracking_id}
      </div>
      <div>File: ${selectedDoc?.file_name}</div>
      </body>
      </html>
    `);
    win.document.close();
    win.print();
  };

  return (
    <>
      {/* ================= CREATE FORM ================= */}
      <Card className="p-4 mb-4">
        <h5>Create Physical QR Tracking</h5>

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

        <Form
          onSubmit={(e) => {
            e.preventDefault();
            generateTracking();
          }}
        >
          <Form.Control
            placeholder="Owner Name"
            className="mb-2"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />

          <Form.Control
            placeholder="Contact (10 digits)"
            className="mb-2"
            value={contact}
            maxLength={10}
            onChange={(e) =>
              setContact(e.target.value.replace(/\D/g, ""))
            }
          />

          <Form.Control
            type="email"
            placeholder="Owner Email"
            className="mb-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <Form.Control
            placeholder="File Name"
            className="mb-2"
            value={fileName}
            onChange={(e) => setFileName(e.target.value)}
          />

          <Form.Control
            type="password"
            placeholder="Owner Password"
            className="mb-2"
            value={ownerPassword}
            onChange={(e) => setOwnerPassword(e.target.value)}
          />

          <Form.Control
            type="file"
            accept=".pdf"
            className="mb-2"
            onChange={(e) => setPdf(e.target.files?.[0] || null)}
          />

          <Form.Check
            label="Restrict Public View"
            className="mb-3"
            checked={restricted}
            onChange={(e) => setRestricted(e.target.checked)}
          />

          <Button type="submit" disabled={loading}>
            {loading ? <Spinner size="sm" /> : "Generate Tracking ID"}
          </Button>
        </Form>

        {tracking && (
          <Alert variant="success" className="mt-3">
            Tracking ID: <b>{tracking?.tracking_id}</b>
          </Alert>
        )}
      </Card>

      {/* ================= HISTORY ================= */}
      <Card className="p-4">
        <h5>Tracking History</h5>

        {history?.length === 0 ? (
          <Alert>No records found</Alert>
        ) : (
          <Table bordered hover responsive>
            <thead>
              <tr>
                <th>ID</th>
                <th>File</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {history?.map((h) => (
                <tr key={h?.id}>
                  <td>{h?.tracking_id}</td>
                  <td>{h?.file_name}</td>
                  <td>
                    {h?.restrict_public_view ? (
                      <Badge bg="danger">Restricted</Badge>
                    ) : (
                      <Badge bg="success">Public</Badge>
                    )}
                  </td>
                  <td>{formatDate(h?.created_at)}</td>
                  <td>
                    <Button size="sm" onClick={() => openView(h)}>
                      View
                    </Button>{" "}
                    <Button
                      size="sm"
                      variant="info"
                      onClick={() => openQR(h)}
                    >
                      QR
                    </Button>{" "}
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => deleteDocument(h)}
                    >
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      {/* ================= PDF MODAL ================= */}
      <Modal show={!!previewUrl} onHide={() => setPreviewUrl(null)} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>PDF Preview</Modal.Title>
        </Modal.Header>
        <Modal.Body style={{ height: "80vh" }}>
          <iframe
            src={previewUrl}
            width="100%"
            height="100%"
            title="PDF Preview"
          />
        </Modal.Body>
      </Modal>

      {/* ================= QR MODAL ================= */}
      <Modal show={qrModal} onHide={() => setQrModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>QR Code</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {qrToken && (
            <>
              <div ref={qrPrintRef} className="text-center">
                <QRCodeCanvas value={shareUrl} size={200} />
                <div className="mt-2">{shareUrl}</div>
              </div>

              <div className="text-center mt-3">
                <Button
                  variant="secondary"
                  className="me-2"
                  onClick={printQR}
                >
                  Print
                </Button>
                <Button variant="danger" onClick={revokeQR}>
                  Revoke
                </Button>
              </div>
            </>
          )}
        </Modal.Body>
      </Modal>
    </>
  );
}
