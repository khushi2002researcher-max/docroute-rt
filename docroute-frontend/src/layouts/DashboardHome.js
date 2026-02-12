
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container, Row, Col, Card, Spinner } from "react-bootstrap";
import Sidebar from "../components/Sidebar";
import { Bar, Pie } from "react-chartjs-2";
import { Outlet } from "react-router-dom";

import "chart.js/auto";

function DashboardHome() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // 🔐 Fetch protected dashboard
  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      navigate("/login");
      return;
    }

    fetch("http://127.0.0.1:8000/auth/dashboard", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Unauthorized");
        return res.json();
      })
      .then((data) => {
        setUser(data.user);
        setLoading(false);
      })
      .catch(() => {
        localStorage.clear();
        navigate("/login");
      });
  }, [navigate]);

  // 📊 Chart Data (static for now – later from backend)
  const uploadData = {
    labels: ["OCR", "AI Summary", "Tracking", "QR"],
    datasets: [
      {
        label: "Documents Processed",
        data: [12, 8, 6, 4],
      },
    ],
  };

  const statusData = {
    labels: ["Completed", "In Progress", "Pending"],
    datasets: [
      {
        data: [15, 6, 3],
      },
    ],
  };

  if (loading)
    return (
      <div className="text-center mt-5">
        <Spinner animation="border" />
        <p>Loading Dashboard...</p>
      </div>
    );

  return (
    
    <div className="d-flex">
      <Sidebar />
      <div className="dashboard-content">
        <Outlet />
      </div>
      
      <div style={{ marginLeft: "240px", width: "100%" }}>
      <Container fluid className="p-4">
        {/* Welcome */}
        <Card className="p-4 mb-4 shadow-sm">
          <h4>Welcome, {user.name} 👋</h4>
          <p className="text-muted">Email: {user.email}</p>
        </Card>

        {/* Stats */}
        <Row className="mb-4">
          <Col md={3}>
            <Card className="p-3 shadow-sm text-center">
              <h6>Total Documents</h6>
              <h3>24</h3>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="p-3 shadow-sm text-center">
              <h6>OCR Completed</h6>
              <h3>12</h3>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="p-3 shadow-sm text-center">
              <h6>AI Summaries</h6>
              <h3>8</h3>
            </Card>
          </Col>
          <Col md={3}>
            <Card className="p-3 shadow-sm text-center">
              <h6>QR Tracked</h6>
              <h3>4</h3>
            </Card>
          </Col>
        </Row>

        {/* Charts */}
        <Row>
          <Col md={7}>
            <Card className="p-3 shadow-sm">
              <h5>Module-wise Usage</h5>
              <Bar data={uploadData} />
            </Card>
          </Col>

          <Col md={5}>
            <Card className="p-3 shadow-sm">
              <h5>Document Status</h5>
              <Pie data={statusData} />
            </Card>
          </Col>
        </Row>
      </Container>
      </div>
    </div>
  );
}


export default DashboardHome;
