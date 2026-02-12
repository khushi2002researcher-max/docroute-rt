import { useState, useEffect, useCallback } from "react";
import api from "../services/api";
import { getErrorMessage } from "../utils/errorHandler";
import {
  Card,
  Button,
  Form,
  Table,
  Spinner,
  Modal,
  Alert,
  Badge,
} from "react-bootstrap";
import { saveAs } from "file-saver";
import { QRCodeCanvas } from "qrcode.react";

/* ===============================
   SAFE DATE FORMATTER
================================ */
const formatDate = (value) => {
  if (!value) return "—";
  const d = new Date(value);
  return isNaN(d.getTime()) ? "—" : d.toLocaleString();
};

/* ===============================
   DIFF RENDERER
================================ */
const renderDiff = (diff = []) =>
  diff?.map((line, i) => {
    if (line?.startsWith("+ "))
      return <div key={i} style={{ background: "#d4f8d4" }}>{line}</div>;
    if (line?.startsWith("- "))
      return <div key={i} style={{ background: "#ffd6d6" }}>{line}</div>;
    return <div key={i}>{line}</div>;
  });

export default function DocumentTracking() {
  /* ===============================
     STATE
  ================================ */
  const [fileName, setFileName] = useState("");
  const [fileUpload, setFileUpload] = useState(null);
  const [newContent, setNewContent] = useState("");

  const [history, setHistory] = useState([]);
  const [previewDoc, setPreviewDoc] = useState(null);

  const [editedContent, setEditedContent] = useState("");
  const [editMode, setEditMode] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [auditLogs, setAuditLogs] = useState([]);
  const [showAuditModal, setShowAuditModal] = useState(false);

  const [versionModal, setVersionModal] = useState(false);
  const [versions, setVersions] = useState([]);
  const [diffData, setDiffData] = useState(null);

  const [showAccessModal, setShowAccessModal] = useState(false);
  const [newAccessPermission, setNewAccessPermission] = useState("view");
  const [sharePassword, setSharePassword] = useState("");
  const [shareLink, setShareLink] = useState(null);
  const [shareToken, setShareToken] = useState(null);

  /* ===============================
     LOAD HISTORY
  ================================ */
  const loadHistory = useCallback(async () => {
    try {
      const res = await api.get("/documents/");
      setHistory(res?.data || []);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  /* ===============================
     CREATE DOCUMENT
  ================================ */
  const handleUpload = async () => {
    if (!fileName.trim()) return setError("File name required");
    if (!fileUpload && !newContent.trim())
      return setError("Enter content or upload file");

    setLoading(true);
    setError("");

    const fd = new FormData();
    fd.append("file_name", fileName);
    if (fileUpload) fd.append("file", fileUpload);
    else fd.append("content", newContent);

    try {
      const res = await api.post("/documents/create", fd);

      setPreviewDoc(res?.data);
      setEditedContent(res?.data?.content || "");
      setNewContent("");
      setFileName("");
      setFileUpload(null);

      setMessage("Document created successfully");
      await loadHistory();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  /* ===============================
     LOAD DOCUMENT
  ================================ */
  const loadFullDocument = async (id) => {
    try {
      const res = await api.get(`/documents/${id}`);
      setPreviewDoc(res?.data);
      setEditedContent(res?.data?.content || "");
      setEditMode(false);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  /* ===============================
     SAVE EDIT
  ================================ */
  const handleSaveEdit = async () => {
    if (!previewDoc) return;

    try {
      await api.put(`/documents/${previewDoc?.id}/update`, {
        content: editedContent,
      });

      await loadFullDocument(previewDoc?.id);
      await loadHistory();
      setEditMode(false);
      setMessage("Document updated successfully");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  /* ===============================
     DELETE DOCUMENT
  ================================ */
  const handleDelete = async (id) => {
    if (!window.confirm("Delete document?")) return;

    try {
      await api.delete(`/documents/${id}`);
      setPreviewDoc(null);
      setMessage("Document deleted");
      await loadHistory();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  /* ===============================
     SHARE
  ================================ */
  const handleShare = async () => {
    if (!previewDoc?.id) return;

    try {
      const res = await api.post(
        `/documents/${previewDoc.id}/share`,
        new URLSearchParams({
          permission: newAccessPermission,
          password: sharePassword || "",
        })
      );

      const baseUrl =
        process.env.REACT_APP_PUBLIC_URL || window.location.origin;

      setShareLink(`${baseUrl}/share/doc/${res?.data?.token}`);
      setShareToken(res?.data?.token);
      setMessage("Share link generated");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const revokeShare = async () => {
    if (!shareToken) return;
    if (!window.confirm("Revoke share link?")) return;

    try {
      await api.post(`/documents/share/${shareToken}/revoke`);
      setShareLink(null);
      setShareToken(null);
      setMessage("Share link revoked");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  /* ===============================
     DOWNLOAD (SAFE BLOB)
  ================================ */
  const downloadFile = async (doc, format) => {
    try {
      const res = await api.get(
        `/documents/${doc?.id}/download?format=${format}`,
        { responseType: "blob" }
      );

      const blob = new Blob([res.data]);
      saveAs(blob, `${doc?.file_name}.${format}`);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  /* ===============================
     UI
  ================================ */
  return (
    <Card className="p-4 shadow-sm">
      <h3>
        📄 Document Tracking{" "}
        {previewDoc?.total_opens !== undefined && (
          <Badge bg="secondary">
            Opens: {previewDoc?.total_opens}
          </Badge>
        )}
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

      {/* CREATE */}
      <Form className="mb-4">
        <Form.Control
          placeholder="File name"
          value={fileName}
          onChange={(e) => setFileName(e.target.value)}
        />

        <Form.Control
          as="textarea"
          rows={3}
          className="mt-2"
          placeholder="Document content"
          value={newContent}
          onChange={(e) => setNewContent(e.target.value)}
        />

        <Form.Control
          type="file"
          className="mt-2"
          onChange={(e) => setFileUpload(e.target.files?.[0] || null)}
        />

        <Button
          className="mt-2"
          style={{ backgroundColor: "#5a83c1" }}
          onClick={handleUpload}
          disabled={loading}
        >
          {loading ? <Spinner size="sm" /> : "Create"}
        </Button>
      </Form>

      {/* PREVIEW */}
      {previewDoc && (
        <Card className="p-3 mb-4">
          {editMode ? (
            <Form.Control
              as="textarea"
              rows={10}
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
            />
          ) : (
            <pre style={{ whiteSpace: "pre-wrap" }}>
              {previewDoc?.content}
            </pre>
          )}

          <div className="d-flex gap-2 flex-wrap">
            {!editMode ? (
              <Button onClick={() => setEditMode(true)}>Edit</Button>
            ) : (
              <Button onClick={handleSaveEdit}>Save</Button>
            )}

            <Button
              variant="warning"
              onClick={() => setShowAccessModal(true)}
            >
              Share
            </Button>

            <Button
              variant="success"
              onClick={() => downloadFile(previewDoc, "pdf")}
            >
              PDF
            </Button>

            <Button
              variant="secondary"
              onClick={() => downloadFile(previewDoc, "docx")}
            >
              DOCX
            </Button>
          </div>
        </Card>
      )}

      {/* HISTORY */}
      <Table bordered hover>
        <thead>
          <tr>
            <th>Tracking ID</th>
            <th>File</th>
            <th>Updated</th>
            <th>Opens</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {history?.map((d) => (
            <tr key={d?.id}>
              <td>{d?.tracking_id}</td>
              <td>{d?.file_name}</td>
              <td>{formatDate(d?.last_updated_at)}</td>
              <td>
                <Badge bg="secondary">{d?.total_opens ?? 0}</Badge>
              </td>
              <td>
                <Button size="sm" onClick={() => loadFullDocument(d?.id)}>
                  View
                </Button>{" "}
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => handleDelete(d?.id)}
                >
                  Delete
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {/* SHARE MODAL */}
      <Modal show={showAccessModal} onHide={() => setShowAccessModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Share Document</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Select
            value={newAccessPermission}
            onChange={(e) => setNewAccessPermission(e.target.value)}
          >
            <option value="view">View</option>
            <option value="edit">Edit</option>
            <option value="download">Download</option>
          </Form.Select>

          <Form.Control
            type="password"
            placeholder="Password (optional)"
            className="mt-2"
            value={sharePassword}
            onChange={(e) => setSharePassword(e.target.value)}
          />

          <Button className="mt-2" onClick={handleShare}>
            Generate Link
          </Button>

          {shareLink && (
            <Alert variant="success" className="mt-3 text-center">
              <div style={{ wordBreak: "break-all" }}>{shareLink}</div>
              <QRCodeCanvas value={shareLink} size={160} includeMargin />
              <Button
                variant="danger"
                className="mt-3"
                onClick={revokeShare}
              >
                Revoke Access
              </Button>
            </Alert>
          )}
        </Modal.Body>
      </Modal>
    </Card>
  );
}
