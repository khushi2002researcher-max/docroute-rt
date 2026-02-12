import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../services/api";
import { getErrorMessage } from "../utils/errorHandler";
import {
  Card,
  Spinner,
  Alert,
  Badge,
  Button,
  Table,
  Form,
} from "react-bootstrap";

/* ================= SAFE DATE ================= */
const formatDate = (v) => {
  if (!v) return "—";
  const d = new Date(v);
  return isNaN(d.getTime()) ? "—" : d.toLocaleString();
};

export default function QRDetails() {
  const { token } = useParams();
  const API_BASE =
    process.env.REACT_APP_API_URL || window.location.origin;

  /* ================= PUBLIC ================= */
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  /* ================= OWNER LOGIN ================= */
  const [showOwnerLogin, setShowOwnerLogin] = useState(false);
  const [ownerPassword, setOwnerPassword] = useState("");
  const [ownerError, setOwnerError] = useState("");
  const [ownerLoading, setOwnerLoading] = useState(false);
  const [ownerData, setOwnerData] = useState(null);

  /* ================= OWNER DATA ================= */
  const [scanHistory, setScanHistory] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [ownerDataLoading, setOwnerDataLoading] = useState(false);

  /* ================= LOAD PUBLIC ================= */
  useEffect(() => {
    let isMounted = true;

    const loadQR = async () => {
      try {
        const res = await api.get(`/qr/scan/${token}`);
        if (isMounted) setData(res.data);
      } catch (err) {
        if (isMounted)
          setError(getErrorMessage(err) || "Invalid or expired QR code");
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    loadQR();
    return () => {
      isMounted = false;
    };
  }, [token]);

  /* ================= LOAD OWNER DATA ================= */
  useEffect(() => {
    if (!ownerData?.id) return;

    let active = true;
    setOwnerDataLoading(true);

    const loadOwnerData = async () => {
      try {
        const [historyRes, auditRes, submissionRes] =
          await Promise.all([
            api.get(`/qr/history/${ownerData.id}`),
            api.get(`/qr/audit/${ownerData.id}`),
            api.get(`/qr/submission/${ownerData.id}`),
          ]);

        if (!active) return;

        setScanHistory(historyRes.data || []);
        setAuditLogs(auditRes.data || []);
        setSubmissions(submissionRes.data || []);
      } catch (err) {
        if (active) setOwnerError(getErrorMessage(err));
      } finally {
        if (active) setOwnerDataLoading(false);
      }
    };

    loadOwnerData();
    return () => {
      active = false;
    };
  }, [ownerData]);

  /* ================= LOADING ================= */
  if (loading) {
    return (
      <div className="d-flex justify-content-center mt-5">
        <Spinner />
      </div>
    );
  }

  if (error) {
    return <Alert variant="danger">{error}</Alert>;
  }

  /* ================= OWNER DASHBOARD ================= */
  if (ownerData) {
    return (
      <div className="container mt-4">
        <Card className="p-4 mb-4">
          <h4>🔐 Owner Dashboard</h4>
          <p><b>Tracking ID:</b> {ownerData.tracking_id}</p>
          <p><b>File:</b> {ownerData.file_name}</p>

          {ownerData.pdf_preview && (
            <iframe
              src={`${API_BASE}${ownerData.pdf_preview}`}
              width="100%"
              height="450"
              title="PDF Preview"
              style={{ border: "1px solid #dee2e6" }}
            />
          )}
        </Card>

        {ownerDataLoading && (
          <div className="text-center my-3">
            <Spinner />
          </div>
        )}

        {/* SUBMISSION HISTORY */}
        <Card className="p-4 mb-4">
          <h5>📦 Submission History</h5>
          {submissions.length === 0 ? (
            <div className="text-muted">No submission history</div>
          ) : (
            <Table bordered>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>To</th>
                  <th>Location</th>
                  <th>Status</th>
                  <th>Submitted</th>
                  <th>Received</th>
                </tr>
              </thead>
              <tbody>
                {submissions.map((s) => (
                  <tr key={s.id}>
                    <td>{s.id}</td>
                    <td>{s.submitted_to}</td>
                    <td>{s.submitted_location}</td>
                    <td>
                      <Badge bg={s.status === "RECEIVED" ? "success" : "warning"}>
                        {s.status}
                      </Badge>
                    </td>
                    <td>{formatDate(s.submitted_at)}</td>
                    <td>{formatDate(s.received_at)}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>

        {/* SCAN HISTORY */}
        <Card className="p-4 mb-4">
          <h5>👁 Scan History</h5>
          {scanHistory.length === 0 ? (
            <div className="text-muted">No scan history</div>
          ) : (
            <Table bordered>
              <thead>
                <tr>
                  <th>Role</th>
                  <th>IP</th>
                  <th>Device</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {scanHistory.map((s) => (
                  <tr key={s.id}>
                    <td>{s.scanned_by}</td>
                    <td>{s.ip_address || "—"}</td>
                    <td>{s.user_agent || "—"}</td>
                    <td>{formatDate(s.scanned_at)}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Card>

        {/* AUDIT LOGS */}
        <Card className="p-4 mb-4">
          <h5>🧾 Audit Logs</h5>
          {auditLogs.length === 0 ? (
            <div className="text-muted">No audit logs</div>
          ) : (
            auditLogs.map((a) => (
              <div key={a.id}>
                <b>{a.action}</b> – {formatDate(a.created_at)}
              </div>
            ))
          )}
        </Card>

        <Button
          variant="secondary"
          onClick={() => {
            setOwnerData(null);
            setOwnerPassword("");
          }}
        >
          Logout Owner
        </Button>
      </div>
    );
  }

  /* ================= PUBLIC VIEW ================= */
  return (
    <div className="container mt-4">
      <Card className="p-4">
        <h4>📦 Physical Document Verification</h4>

        <p>
          <b>Status:</b>{" "}
          {data?.verified ? (
            <Badge bg="success">Verified</Badge>
          ) : (
            <Badge bg="danger">Restricted</Badge>
          )}
        </p>

        <Alert variant={data?.verified ? "success" : "warning"}>
          {data?.message}
        </Alert>

        <h6>📇 Owner Details</h6>
        <p><b>Name:</b> {data?.owner_name || "—"}</p>
        <p><b>Email:</b> {data?.owner_email || "—"}</p>
        <p><b>Contact:</b> {data?.owner_contact || "—"}</p>

        <Button onClick={() => setShowOwnerLogin(!showOwnerLogin)}>
          🔐 Use Credentials to Login
        </Button>

        {showOwnerLogin && (
          <div className="mt-3">
            <Form.Control
              type="password"
              placeholder="Owner Password"
              value={ownerPassword}
              onChange={(e) => setOwnerPassword(e.target.value)}
              disabled={ownerLoading}
            />

            {ownerError && (
              <Alert variant="danger" className="mt-2">
                {ownerError}
              </Alert>
            )}

            <Button
              className="mt-2"
              disabled={ownerLoading}
              onClick={async () => {
                if (ownerLoading) return;

                try {
                  setOwnerLoading(true);
                  setOwnerError("");

                  const r = await api.post(
                    `/qr/owner-login/${token}`,
                    { password: ownerPassword }
                  );

                  setOwnerData(r.data);
                  setOwnerPassword("");
                } catch (err) {
                  setOwnerError(getErrorMessage(err) || "Invalid password");
                } finally {
                  setOwnerLoading(false);
                }
              }}
            >
              {ownerLoading ? <Spinner size="sm" /> : "Unlock"}
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}
