import { Container, Row, Col, Button } from "react-bootstrap";
import { Link } from "react-router-dom";
import { Suspense, lazy } from "react";
import { Helmet } from "react-helmet";
import NavbarMenu from "../components/NavbarMenu";
import "../styles/Home.css";
import "../styles/Navbar.css";

/* ===============================
   LAZY LOAD HEAVY COMPONENTS
================================ */
const TextType = lazy(() => import("../components/TextType"));
const ScrambledText = lazy(() => import("../components/ScrambledText"));
const SpotlightCard = lazy(() => import("../components/SpotlightCard"));
const Orb = lazy(() => import("../components/Orb"));
const Stepper = lazy(() => import("../components/Stepper"));
const Step = lazy(() =>
  import("../components/Stepper").then((m) => ({ default: m.Step }))
);

function Home() {
  return (
    <>
      {/* ================= SEO ================= */}
      <Helmet>
        <title>DocRoute-RT | Smart Document Management</title>
        <meta
          name="description"
          content="DocRoute-RT is a secure AI-powered document management platform with OCR, QR tracking, audit logs, and workflow automation."
        />
      </Helmet>

      <NavbarMenu />

      {/* ================= HERO SECTION ================= */}
      <Container
        fluid
        className="hero-section text-center position-relative overflow-hidden"
      >
        <div className="hero-orb-bg">
          <Suspense fallback={null}>
            <Orb backgroundColor="#000000" />
          </Suspense>
        </div>

        <div className="hero-content">
          <h1 className="display-4 fw-bold">
            <Suspense fallback="Smart & Secure Document Management">
              <TextType
                text="Smart & Secure Document Management"
                typingSpeed={60}
                pauseDuration={2000}
                loop={false}
                showCursor
                cursorCharacter="|"
                className="hero-title-type"
              />
            </Suspense>
          </h1>

          <p className="lead mt-3">
            <Suspense fallback={null}>
              <TextType
                text={[
                  "OCR • AI Summarization • QR Tracking",
                  "Secure Sharing • Audit Logs • Workflow Automation",
                ]}
                typingSpeed={45}
                deletingSpeed={30}
                pauseDuration={1500}
                loop
                showCursor
                cursorCharacter="_"
                className="hero-subtitle-type"
              />
            </Suspense>
          </p>

          <div className="mt-4">
            <Link to="/register">
              <Button className="get-btn fancy-btn me-3">
                <span className="btn-text-one">Get Started</span>
                <span className="btn-text-two">Create Account</span>
              </Button>
            </Link>

            <Link to="/about">
              <Button variant="outline-light">
                Learn More
              </Button>
            </Link>
          </div>
        </div>
      </Container>

      {/* ================= ABOUT PROJECT ================= */}
      <Container className="py-5">
        <h2 className="section-title text-center mb-4">
          About DocRoute-RT
        </h2>

        <Suspense fallback={null}>
          <ScrambledText
            className="project-desc text-center"
            radius={120}
            duration={1.1}
            speed={0.4}
            scrambleChars=".:"
          >
            DocRoute-RT is a secure document management platform designed to
            digitize, analyze, track, and audit documents using OCR,
            Artificial Intelligence, and QR-based physical tracking.
            Every document view, scan, and transfer is fully traceable
            with detailed logs and analytics.
          </ScrambledText>
        </Suspense>
      </Container>

      {/* ================= CORE FEATURES ================= */}
      <Container id="features" className="py-5 bg-light">
        <h2 className="section-title text-center mb-5">
          Core Features
        </h2>

        <Row className="g-4">
          {[
            {
              title: "📄 OCR Digitization",
              desc: "Convert scanned PDFs and images into machine-readable text with high accuracy.",
              color: "rgba(0, 229, 255, 0.25)",
            },
            {
              title: "🤖 AI Summarization & Tagging",
              desc: "Automatically summarize documents and generate intelligent tags for classification.",
              color: "rgba(34, 197, 94, 0.25)",
            },
            {
              title: "🔐 Secure Authentication",
              desc: "JWT-based authentication with encryption and role-based access control.",
              color: "rgba(168, 85, 247, 0.25)",
            },
            {
              title: "🆔 QR Physical Tracking",
              desc: "Generate QR codes for physical documents and track scans in real time.",
              color: "rgba(251, 146, 60, 0.25)",
            },
            {
              title: "📤 Submission Logs",
              desc: "Track submissions, transfers, receiving status, and remarks.",
              color: "rgba(14, 165, 233, 0.25)",
            },
            {
              title: "📊 Audit Logs & Analytics",
              desc: "Maintain complete audit trails including actions and history.",
              color: "rgba(239, 68, 68, 0.25)",
            },
          ].map((feature, index) => (
            <Col md={4} key={index}>
              <Suspense fallback={null}>
                <SpotlightCard spotlightColor={feature.color}>
                  <h4>{feature.title}</h4>
                  <p>{feature.desc}</p>
                </SpotlightCard>
              </Suspense>
            </Col>
          ))}
        </Row>
      </Container>

      {/* ================= HOW IT WORKS ================= */}
      <Container id="how" className="py-5">
        <h2 className="section-title text-center mb-4">
          How It Works
        </h2>

        <Suspense fallback={null}>
          <Stepper
            initialStep={1}
            backButtonText="Previous"
            nextButtonText="Next"
          >
            <Step>
              <h4>1️⃣ Upload Document</h4>
              <p>Upload your document securely into the system.</p>
            </Step>

            <Step>
              <h4>2️⃣ Process with OCR & AI</h4>
              <p>The document is analyzed using OCR and AI.</p>
            </Step>

            <Step>
              <h4>3️⃣ Generate QR Code</h4>
              <p>A unique QR code links physical and digital copies.</p>
            </Step>

            <Step>
              <h4>4️⃣ Track & Audit</h4>
              <p>Monitor scans and maintain a full audit log.</p>
            </Step>

            <Step>
              <h4>5️⃣ Securely Share</h4>
              <p>Export and share documents securely.</p>
            </Step>
          </Stepper>
        </Suspense>
      </Container>

      {/* ================= FOOTER ================= */}
      <footer className="footer text-center py-4">
        <p className="mb-1">© 2026 DocRoute-RT</p>
        <small>
          Final Year Project • Secure Document Routing & Tracking System
        </small>
      </footer>
    </>
  );
}

export default Home;
