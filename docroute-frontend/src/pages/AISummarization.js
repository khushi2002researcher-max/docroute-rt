import { useState, useEffect, useCallback } from "react";
import api from "../services/api";
import { getErrorMessage } from "../utils/errorHandler";
import Loader from "../components/ui/Loader";
import {
  Card,
  Button,
  Form,
  Badge,
  Table,
  Alert,
} from "react-bootstrap";

function AISummarize() {
  const [fileUpload, setFileUpload] = useState(null);
  const [summary, setSummary] = useState("");
  const [tags, setTags] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDoc, setSelectedDoc] = useState(null);

  const [language, setLanguage] = useState("english");
  const [length, setLength] = useState("short");
  const [format, setFormat] = useState("paragraph");

  /* ===============================
     LOAD HISTORY
  ================================ */
  const loadHistory = useCallback(async () => {
    try {
      setPageLoading(true);
      const res = await api.get("/ai/history");
      setHistory(res?.data || []);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setPageLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  /* ===============================
     FILE ANALYSIS
  ================================ */
  const handleAnalyze = async () => {
    if (!fileUpload) {
      setError("Please upload a file");
      return;
    }

    setError(null);
    setLoading(true);

    const formData = new FormData();
    formData.append("upload_file", fileUpload);
    formData.append("language", language);
    formData.append("length", length);
    formData.append("format", format);

    try {
      const res = await api.post("/ai/analyze-file", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setSummary(res?.data?.summary || "");
      setTags(res?.data?.tags || []);
      setSelectedDoc(null);

      // reset form
      setFileUpload(null);
      setLanguage("english");
      setLength("short");
      setFormat("paragraph");

      await loadHistory();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  /* ===============================
     DELETE RECORD
  ================================ */
  const handleDelete = async (id) => {
    if (!window.confirm("Delete this record?")) return;

    try {
      await api.delete(`/ai/${id}`);
      setHistory((prev) => prev?.filter((doc) => doc.id !== id));

      if (selectedDoc?.id === id) {
        setSummary("");
        setTags([]);
        setSelectedDoc(null);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  /* ===============================
     VIEW RECORD
  ================================ */
  const handleView = (doc) => {
    setSummary(doc?.summary || "");
    setTags(doc?.tags || []);
    setSelectedDoc(doc);
  };

  /* ===============================
     GENERIC DOWNLOAD HELPER
  ================================ */
  const downloadFile = async (url, filename, type) => {
    try {
      const res = await api.get(url, { responseType: "blob" });

      const blob = new Blob([res.data], { type });
      const fileURL = window.URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = fileURL;
      link.download = filename;
      link.click();

      window.URL.revokeObjectURL(fileURL);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  /* ===============================
     RENDER
  ================================ */
  if (pageLoading) return <Loader />;

  return (
    <Card className="p-4 shadow-sm">
      <h3 className="mb-4">AI Summarization + Auto-Tagging</h3>

      {error && (
        <Alert variant="danger" onClose={() => setError(null)} dismissible>
          {error}
        </Alert>
      )}

      {/* FILE UPLOAD */}
      <Form.Control
        type="file"
        accept=".pdf,.docx,.txt"
        className="mb-3"
        onChange={(e) => setFileUpload(e.target.files?.[0] || null)}
      />

      {/* OPTIONS */}
      <div className="d-flex gap-3 mb-3">
        <Form.Select value={language} onChange={(e) => setLanguage(e.target.value)}>
          <option value="english">English</option>
          <option value="hindi">Hindi</option>
        </Form.Select>

        <Form.Select value={length} onChange={(e) => setLength(e.target.value)}>
          <option value="short">Short</option>
          <option value="medium">Medium</option>
          <option value="long">Long</option>
          <option value="detailed">Detailed</option>
        </Form.Select>

        <Form.Select value={format} onChange={(e) => setFormat(e.target.value)}>
          <option value="paragraph">Paragraph</option>
          <option value="bullets">Bullet Points</option>
        </Form.Select>
      </div>

      <Button
        style={{ backgroundColor: "#5a83c1", borderColor: "#5a83c1" }}
        onClick={handleAnalyze}
        disabled={loading}
      >
        {loading ? "Processing..." : "Analyze"}
      </Button>

      {/* SUMMARY PREVIEW */}
      {summary && (
        <Card className="mt-4 p-3">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <strong>Preview</strong>

            {selectedDoc && (
              <div>
                <Button
                  size="sm"
                  variant="secondary"
                  className="me-2"
                  onClick={() =>
                    downloadFile(
                      `/ai/download/pdf/${selectedDoc?.id}`,
                      `${selectedDoc?.file_name}_summary.pdf`,
                      "application/pdf"
                    )
                  }
                >
                  Download PDF
                </Button>

                {selectedDoc?.language?.toLowerCase() === "english" && (
                  <Button
                    size="sm"
                    variant="success"
                    onClick={() =>
                      downloadFile(
                        `/ai/download/docx/${selectedDoc?.id}`,
                        `${selectedDoc?.file_name}_summary.docx`,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                      )
                    }
                  >
                    Download DOCX
                  </Button>
                )}
              </div>
            )}
          </div>

          <p>{summary}</p>

          {tags?.length > 0 && (
            <div className="mt-2">
              {tags?.map((tag, i) => (
                <Badge key={i} bg="secondary" className="me-1">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* HISTORY */}
      <h5 className="mt-5">History</h5>

      <Table bordered hover responsive>
        <thead>
          <tr>
            <th>File</th>
            <th>Summary</th>
            <th>Tags</th>
            <th>Language</th>
            <th>Length</th>
            <th>Format</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {history?.length > 0 ? (
            history?.map((doc) => (
              <tr key={doc?.id}>
                <td>{doc?.file_name}</td>
                <td style={{ maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {doc?.summary}
                </td>
                <td>
                  {doc?.tags?.map((t, i) => (
                    <Badge key={i} bg="info" className="me-1">
                      {t}
                    </Badge>
                  ))}
                </td>
                <td>{doc?.language}</td>
                <td>{doc?.length}</td>
                <td>{doc?.format}</td>
                <td>
                  <Button size="sm" onClick={() => handleView(doc)}>
                    View
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    className="ms-2"
                    onClick={() => handleDelete(doc?.id)}
                  >
                    Delete
                  </Button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="7" className="text-center">
                No history found
              </td>
            </tr>
          )}
        </tbody>
      </Table>
    </Card>
  );
}

export default AISummarize;
