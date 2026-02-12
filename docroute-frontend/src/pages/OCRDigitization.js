import { useState, useEffect, useCallback } from "react";
import { Container, Card, Button, Form, Table, Alert, Spinner } from "react-bootstrap";
import jsPDF from "jspdf";
import api from "../services/api";
import { getErrorMessage } from "../utils/errorHandler";

/* ===============================
   SAFE DATE FORMATTER
================================ */
const formatDate = (value) => {
  if (!value) return "—";
  const d = new Date(value);
  return isNaN(d.getTime()) ? "—" : d.toLocaleString();
};

function OCRDigitization() {
  const [file, setFile] = useState(null);
  const [history, setHistory] = useState([]);
  const [selectedText, setSelectedText] = useState("");
  const [selectedFile, setSelectedFile] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  /* ============================
     Fetch OCR History
  ============================ */
  const fetchHistory = useCallback(async () => {
    try {
      const res = await api.get("/ocr/history");
      setHistory(res?.data || []);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  /* ============================
     Upload File for OCR
  ============================ */
  const handleUpload = async () => {
    if (loading) return;

    if (!file) {
      setError("Please select a file first.");
      return;
    }

    if (!file.type?.startsWith("image/")) {
      setError("Only image files are allowed for OCR.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post("/ocr/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setSelectedText(res?.data?.extracted_text || "");
      setSelectedFile(res?.data?.filename || "");
      setFile(null);
      setMessage("OCR completed successfully");

      await fetchHistory();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  /* ============================
     View OCR Record
  ============================ */
  const viewRecord = async (id, filename) => {
    try {
      const res = await api.get(`/ocr/history/${id}`);
      setSelectedText(res?.data?.extracted_text || "");
      setSelectedFile(filename || "");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  /* ============================
     Delete OCR Record
  ============================ */
  const deleteRecord = async (id) => {
    if (!window.confirm("Delete this OCR record?")) return;

    try {
      await api.delete(`/ocr/history/${id}`);

      setHistory((prev) => prev.filter((item) => item.id !== id));

      if (history.find((h) => h.id === id)) {
        setSelectedText("");
        setSelectedFile("");
      }

      setMessage("Record deleted successfully");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  /* ============================
     Download TXT
  ============================ */
  const downloadTXT = () => {
    if (!selectedText) return;

    const blob = new Blob([selectedText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = `${selectedFile || "ocr_text"}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  /* ============================
     Download PDF
  ============================ */
  const downloadPDF = () => {
    if (!selectedText) return;

    const pdf = new jsPDF();
    const lines = pdf.splitTextToSize(selectedText, 180);
    pdf.text(lines, 10, 10);
    pdf.save(`${selectedFile || "ocr_text"}.pdf`);
  };

  return (
    <Container className="mt-4">
      <Card className="p-4 shadow-sm glass-hover-card">
        <h3>📄 OCR Digitization</h3>

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

        <Form.Control
          type="file"
          accept="image/*"
          className="mt-3"
          onChange={(e) => {
            setFile(e.target.files?.[0] || null);
            setError("");
          }}
          disabled={loading}
        />

        <Button
          className="mt-3"
          style={{ backgroundColor: "#5a83c1", borderColor: "#5a83c1" }}
          onClick={handleUpload}
          disabled={loading}
        >
          {loading ? <Spinner size="sm" /> : "Upload & OCR"}
        </Button>
      </Card>

      {/* OCR HISTORY */}
      <Card className="mt-4 p-3 shadow-sm glass-hover-card">
        <h5>📜 OCR History</h5>

        <Table hover responsive className="mt-3">
          <thead>
            <tr>
              <th>File</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {history?.length === 0 ? (
              <tr>
                <td colSpan="3" className="text-center">
                  No records found
                </td>
              </tr>
            ) : (
              history?.map((item) => (
                <tr key={item?.id}>
                  <td>{item?.filename}</td>
                  <td>{formatDate(item?.created_at)}</td>
                  <td>
                    <Button
                      size="sm"
                      variant="info"
                      className="me-2"
                      onClick={() =>
                        viewRecord(item?.id, item?.filename)
                      }
                    >
                      View
                    </Button>

                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => deleteRecord(item?.id)}
                    >
                      Delete
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </Table>
      </Card>

      {/* OCR PREVIEW */}
      {selectedText && (
        <Card className="mt-4 p-3 shadow-sm glass-hover-card">
          <h5>📝 OCR Text Preview</h5>

          <pre
            style={{
              whiteSpace: "pre-wrap",
              maxHeight: "300px",
              overflowY: "auto",
              background: "#f8f9fa",
              padding: "10px",
              borderRadius: "5px",
            }}
          >
            {selectedText}
          </pre>

          <div className="mt-3">
            <Button
              variant="success"
              className="me-2"
              onClick={downloadTXT}
            >
              Download TXT
            </Button>

            <Button variant="secondary" onClick={downloadPDF}>
              Download PDF
            </Button>
          </div>
        </Card>
      )}
    </Container>
  );
}

export default OCRDigitization;
