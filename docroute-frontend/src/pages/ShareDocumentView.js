import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import api from "../services/api";
import {
  Card,
  Spinner,
  Alert,
  Form,
  Button,
  Badge,
} from "react-bootstrap";

export default function ShareDocumentView() {
  const { token } = useParams();

  /* ================= STATE ================= */
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [docData, setDocData] = useState(null);

  const [password, setPassword] = useState("");
  const [passwordRequired, setPasswordRequired] =
    useState(false);
  const [unlocking, setUnlocking] = useState(false);

  const [editMode, setEditMode] = useState(false);
  const [editedContent, setEditedContent] = useState("");
  const [saving, setSaving] = useState(false);

  /* ================= LOAD DOCUMENT ================= */
  const loadDocument = async (pwd = "") => {
    try {
      setLoading(true);
      setError("");

      const trimmedPwd = pwd.trim();

      const res = await api.get(
        `/documents/share/${token}`,
        {
          params: trimmedPwd
            ? { password: trimmedPwd }
            : {},
        }
      );

      setDocData(res.data);
      setEditedContent(
        res.data?.document?.content || ""
      );
      setPasswordRequired(false);
    } catch (err) {
      const detail =
        err.response?.data?.detail || "";

      if (
        detail.toLowerCase().includes("password")
      ) {
        setPasswordRequired(true);
      } else {
        setError(detail || "Invalid or expired link");
      }
    } finally {
      setLoading(false);
      setUnlocking(false);
    }
  };

  useEffect(() => {
    if (!token) {
      setError("Invalid share link");
      setLoading(false);
      return;
    }

    loadDocument();
    // eslint-disable-next-line
  }, [token]);

  /* ================= LOADING ================= */
  if (loading) {
    return (
      <div className="d-flex justify-content-center mt-5">
        <Spinner animation="border" />
      </div>
    );
  }

  /* ================= ERROR ================= */
  if (error) {
    return (
      <Alert
        variant="danger"
        className="m-4 text-center"
      >
        {error}
      </Alert>
    );
  }

  /* ================= PASSWORD VIEW ================= */
  if (passwordRequired && !docData) {
    return (
      <Card
        className="p-4 m-4 mx-auto shadow-sm"
        style={{ maxWidth: 420 }}
      >
        <h5 className="mb-3 text-center">
          🔒 Password Required
        </h5>

        <Form.Control
          type="password"
          placeholder="Enter password"
          value={password}
          onChange={(e) =>
            setPassword(e.target.value)
          }
          className="mb-3"
        />

        <Button
          className="w-100"
          disabled={!password || unlocking}
          onClick={() => {
            if (unlocking) return;
            setUnlocking(true);
            loadDocument(password);
          }}
        >
          {unlocking ? (
            <>
              <Spinner
                size="sm"
                className="me-2"
              />
              Unlocking...
            </>
          ) : (
            "Unlock"
          )}
        </Button>
      </Card>
    );
  }

  /* ================= MAIN VIEW ================= */
  const { document, watermark, permission } =
    docData || {};

  if (!document) {
    return (
      <Alert
        variant="warning"
        className="m-4 text-center"
      >
        Document not available
      </Alert>
    );
  }

  return (
    <div className="container mt-4">
      <Card className="p-4 shadow-sm">
        <div className="d-flex justify-content-between align-items-center">
          <h4>{document.file_name}</h4>
          <Badge bg="secondary">
            {permission?.toUpperCase()}
          </Badge>
        </div>

        <hr />

        {/* Watermark */}
        {watermark?.text && (
          <div
            style={{
              fontSize: 12,
              opacity:
                watermark?.opacity ?? 0.15,
              marginBottom: 10,
            }}
          >
            {watermark.text}
          </div>
        )}

        {/* Document Content */}
        {permission === "edit" &&
        editMode ? (
          <Form.Control
            as="textarea"
            rows={12}
            value={editedContent}
            disabled={saving}
            onChange={(e) =>
              setEditedContent(e.target.value)
            }
          />
        ) : (
          <pre
            style={{
              whiteSpace: "pre-wrap",
              minHeight: 200,
            }}
          >
            {document.content ||
              "No preview available"}
          </pre>
        )}

        {/* ================= EDIT ================= */}
        {permission === "edit" && (
          <div className="mt-3">
            {!editMode ? (
              <Button
                onClick={() =>
                  setEditMode(true)
                }
              >
                Edit
              </Button>
            ) : (
              <Button
                disabled={saving}
                onClick={async () => {
                  if (saving) return;

                  try {
                    setSaving(true);

                    await api.put(
                      `/documents/share/${token}/edit`,
                      new URLSearchParams({
                        content:
                          editedContent,
                      })
                    );

                    setDocData((prev) => ({
                      ...prev,
                      document: {
                        ...prev.document,
                        content:
                          editedContent,
                      },
                    }));

                    setEditMode(false);
                  } catch {
                    alert(
                      "Failed to save changes"
                    );
                  } finally {
                    setSaving(false);
                  }
                }}
              >
                {saving ? (
                  <>
                    <Spinner
                      size="sm"
                      className="me-2"
                    />
                    Saving...
                  </>
                ) : (
                  "Save"
                )}
              </Button>
            )}
          </div>
        )}

        {/* ================= DOWNLOAD ================= */}
        {permission === "download" && (
          <div className="mt-3 d-flex gap-2">
            <Button
              variant="success"
              onClick={async () => {
                const res =
                  await api.get(
                    `/documents/share/${token}/download?format=docx`,
                    { responseType: "blob" }
                  );

                const blob =
                  new Blob([res.data]);
                const url =
                  URL.createObjectURL(blob);

                const a =
                  document.createElement("a");
                a.href = url;
                a.download =
                  `${document.file_name}.docx`;
                a.click();

                URL.revokeObjectURL(url);
              }}
            >
              Download DOCX
            </Button>

            <Button
              variant="danger"
              onClick={async () => {
                const res =
                  await api.get(
                    `/documents/share/${token}/download?format=pdf`,
                    { responseType: "blob" }
                  );

                const blob =
                  new Blob([res.data]);
                const url =
                  URL.createObjectURL(blob);

                const a =
                  document.createElement("a");
                a.href = url;
                a.download =
                  `${document.file_name}.pdf`;
                a.click();

                URL.revokeObjectURL(url);
              }}
            >
              Download PDF
            </Button>
          </div>
        )}

        {/* ================= VIEW ONLY ================= */}
        {permission !== "edit" &&
          permission !== "download" && (
            <Alert
              variant="info"
              className="mt-3"
            >
              This document is shared with{" "}
              <strong>
                {permission}
              </strong>{" "}
              access.
            </Alert>
          )}
      </Card>
    </div>
  );
}
