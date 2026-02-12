import { useEffect, useState, useCallback } from "react";
import api from "../services/api";
import { getErrorMessage } from "../utils/errorHandler";
import Loader from "../components/ui/Loader";
import {
  Container,
  Row,
  Col,
  Card,
  Alert,
  Badge,
} from "react-bootstrap";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
} from "recharts";

/* =========================
   CONSTANTS
========================= */

const COLORS = ["#0d6efd", "#198754", "#ffc107", "#dc3545"];

/* =========================
   ANALYTICS DASHBOARD
========================= */

export default function Analytics() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [user, setUser] = useState(null);
  const [overview, setOverview] = useState({});
  const [workflow, setWorkflow] = useState({});
  const [reminders, setReminders] = useState({});
  const [systemHealth, setSystemHealth] = useState({});
  const [docCodeStats, setDocCodeStats] = useState({});

  /* =========================
     LOAD ANALYTICS (SAFE)
  ========================= */

  const loadAnalytics = useCallback(async (isBackground = false) => {
    try {
      if (isBackground) setRefreshing(true);
      else setLoading(true);

      const [
        overviewRes,
        workflowRes,
        reminderRes,
        healthRes,
        docCodeRes,
      ] = await Promise.all([
        api.get("/analytics/overview"),
        api.get("/analytics/workflow"),
        api.get("/analytics/reminders"),
        api.get("/analytics/system-health"),
        api.get("/analytics/doc-code"),
      ]);

      setOverview(overviewRes?.data || {});
      setWorkflow(workflowRes?.data || {});
      setReminders(reminderRes?.data || {});
      setSystemHealth(healthRes?.data || {});
      setDocCodeStats(docCodeRes?.data || {});

      try {
        const userRes = await api.get("/auth/me");
        setUser(userRes?.data || null);
      } catch {
        setUser(null);
      }

      setError("");
    } catch (err) {
      if (!isBackground) {
        setError(getErrorMessage(err));
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  /* =========================
     INITIAL LOAD + AUTO REFRESH
  ========================= */

  useEffect(() => {
    loadAnalytics();

    const interval = setInterval(() => {
      loadAnalytics(true); // silent background refresh
    }, 60000);

    return () => clearInterval(interval);
  }, [loadAnalytics]);

  /* =========================
     RENDER STATES
  ========================= */

  if (loading) return <Loader />;

  if (error)
    return (
      <Alert variant="danger" className="mt-4">
        {error}
      </Alert>
    );

  return (
    <Container fluid className="mt-4">

      {/* ================= USER HEADER ================= */}
      <Card className="mb-4 shadow-sm">
        <Card.Body>
          <Row>
            <Col>
              <h4 className="mb-1">
                Welcome, <strong>{user?.full_name || "User"}</strong>
              </h4>
              <div className="text-muted">{user?.email}</div>
            </Col>
            <Col className="text-end">
              <Badge bg="primary">
                Analytics Dashboard {refreshing && "• Updating"}
              </Badge>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* ================= KPI OVERVIEW ================= */}
      <Row className="mb-4 g-3">
        <Kpi title="Total Documents" value={overview?.total_documents} />
        <Kpi title="OCR Processed" value={overview?.ocr_processed} />
        <Kpi title="AI Analyzed" value={overview?.ai_analyzed} />
        <Kpi title="Active Deadlines" value={overview?.active_deadlines} />
        <Kpi title="Pending Reminders" value={overview?.pending_reminders} />
        <Kpi
          title="Missed Deadlines"
          value={overview?.missed_deadlines}
          danger
        />
      </Row>

      {/* ================= WORKFLOW ================= */}
      <Row className="mb-4 g-4">
        <ChartCard title="AI Workflow Routing">
          {workflow?.routing?.length ? (
            <PieChartView data={workflow.routing} />
          ) : (
            <EmptyState />
          )}
        </ChartCard>

        <ChartCard title="Deadlines by Priority">
          {workflow?.deadlines?.length ? (
            <BarChartView data={workflow.deadlines} />
          ) : (
            <EmptyState />
          )}
        </ChartCard>
      </Row>

      {/* ================= REMINDERS ================= */}
      <Row className="mb-4 g-4">
        <ChartCard title="Reminder Status">
          {reminders?.data?.length ? (
            <PieChartView data={reminders.data} valueKey="count" nameKey="status" />
          ) : (
            <EmptyState />
          )}
        </ChartCard>

        <Col md={6}>
          <Card className="shadow-sm text-center">
            <Card.Header>Failed Reminders Today</Card.Header>
            <Card.Body>
              <h2 className="text-danger">
                {reminders?.failed_today ?? 0}
              </h2>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* ================= DOC CODE ================= */}
      <Row className="mb-4 g-4">
        <ChartCard title="Document Exchange">
          <PieChartView
            data={[
              { label: "Sent", value: docCodeStats?.sent_total ?? 0 },
              { label: "Received", value: docCodeStats?.received_total ?? 0 },
            ]}
          />
        </ChartCard>

        <ChartCard title="Code Usage">
          <BarChartView
            data={[
              { name: "Used", count: docCodeStats?.used_codes ?? 0 },
              { name: "Pending", count: docCodeStats?.pending_codes ?? 0 },
            ]}
          />
        </ChartCard>
      </Row>

      {/* ================= SYSTEM HEALTH ================= */}
      <Card className="shadow-sm mb-5">
        <Card.Header>System Health</Card.Header>
        <Card.Body>
          <Row>
            {systemHealth?.services?.length ? (
              systemHealth.services.map((s, i) => (
                <Col md={3} key={i}>
                  <Card className="text-center mb-3">
                    <Card.Body>
                      <div className="fw-bold">{s?.service}</div>
                      <Badge bg={s?.status === "OK" ? "success" : "danger"}>
                        {s?.status}
                      </Badge>
                    </Card.Body>
                  </Card>
                </Col>
              ))
            ) : (
              <EmptyState />
            )}
          </Row>
        </Card.Body>
      </Card>

    </Container>
  );
}

/* =========================
   REUSABLE COMPONENTS
========================= */

function Kpi({ title, value, danger }) {
  return (
    <Col lg={2} md={4} sm={6}>
      <Card className="shadow-sm border-0 text-center">
        <Card.Body>
          <div className="text-muted small">{title}</div>
          <h4 className={`fw-bold ${danger ? "text-danger" : "text-primary"}`}>
            {value ?? 0}
          </h4>
        </Card.Body>
      </Card>
    </Col>
  );
}

function ChartCard({ title, children }) {
  return (
    <Col md={6}>
      <Card className="shadow-sm">
        <Card.Header>{title}</Card.Header>
        <Card.Body style={{ height: 260 }}>
          {children}
        </Card.Body>
      </Card>
    </Col>
  );
}

function PieChartView({ data, valueKey = "value", nameKey = "label" }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          dataKey={valueKey}
          nameKey={nameKey}
          outerRadius={90}
        >
          {data?.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  );
}

function BarChartView({ data }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <XAxis dataKey={data?.[0]?.priority ? "priority" : "name"} />
        <YAxis />
        <Tooltip />
        <Bar
          dataKey={data?.[0]?.count ? "count" : "value"}
          fill="#dc3545"
          radius={[6, 6, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

function EmptyState() {
  return (
    <div className="text-center text-muted mt-4">
      No data available
    </div>
  );
}
