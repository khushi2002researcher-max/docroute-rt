import { Container, Row, Col } from "react-bootstrap";
import { FaShieldAlt, FaEye, FaRocket } from "react-icons/fa";
import { Suspense, lazy, useMemo } from "react";
import { Helmet } from "react-helmet";
import NavbarMenu from "../components/NavbarMenu";
import BlurText from "../components/BlurText";
import Loader from "../components/ui/Loader";
import "../styles/About.css";

/* ===============================
   LAZY LOAD HEAVY COMPONENT
================================ */
const Orb = lazy(() => import("../components/Orb"));

function About() {
  /* ===============================
     DATA-DRIVEN BENEFITS
  ================================ */
  const benefits = useMemo(
    () => [
      {
        icon: <FaShieldAlt size={40} className="mb-3 text-primary" />,
        title: "Enterprise-Level Security",
        description:
          "Control who can view your documents using secure authentication and protected sharing methods.",
      },
      {
        icon: <FaEye size={40} className="mb-3 text-primary" />,
        title: "Full Visibility",
        description:
          "Monitor every view, download, and scan — ensuring complete transparency and accountability.",
      },
      {
        icon: <FaRocket size={40} className="mb-3 text-primary" />,
        title: "Fast & Intelligent",
        description:
          "AI-powered summarization and tagging make document management faster and more efficient.",
      },
    ],
    []
  );

  return (
    <>
      {/* ================= SEO ================= */}
      <Helmet>
        <title>About | DocRoute-RT</title>
        <meta
          name="description"
          content="DocRoute-RT is an AI-powered document management platform with secure tracking, OCR extraction, and QR-based verification."
        />
      </Helmet>

      <NavbarMenu />

      {/* ================= HERO SECTION ================= */}
      <section className="about-hero">
        <div className="about-orb-bg">
          <Suspense fallback={null}>
            <Orb
              backgroundColor="#000000"
              hoverIntensity={0.15}
              rotateOnHover
            />
          </Suspense>
        </div>

        <div className="about-hero-content">
          <h1 className="display-5 fw-bold">
            Smarter Document Control Starts Here
          </h1>

          <BlurText
            text="AI-powered document management with secure tracking, QR verification, and real-time transparency."
            delay={120}
            animateBy="words"
            direction="top"
            className="lead mt-3 about-blur-text"
          />
        </div>
      </section>

      {/* ================= MAIN CONTENT ================= */}
      <Container className="py-5">

        {/* WHY / WHAT SECTION */}
        <Row className="g-4">
          <Col md={6}>
            <div className="why-card">
              <h4>Why DocRoute-RT?</h4>
              <p>
                DocRoute-RT gives you complete visibility and control over your
                documents. Every action is securely recorded — so you always know
                who accessed what, and when.
              </p>
            </div>
          </Col>

          <Col md={6}>
            <div className="why-card">
              <h4>What You Can Do</h4>
              <p>
                Upload documents, extract text using OCR, generate AI summaries,
                create secure share links, and track physical documents using QR
                codes — all from one unified platform.
              </p>
            </div>
          </Col>
        </Row>

        {/* HOW IT WORKS */}
        <Row className="mt-5">
          <Col>
            <h4>How It Works</h4>
            <ul className="about-list mt-3">
              <li>Upload your document securely.</li>
              <li>OCR extracts readable content.</li>
              <li>AI generates summaries and smart tags.</li>
              <li>QR code links physical and digital copies.</li>
              <li>Track every access in real time.</li>
            </ul>
          </Col>
        </Row>

        {/* BENEFITS SECTION (Dynamic) */}
        <Row className="g-4 mt-5 text-center">
          {benefits?.map((item, index) => (
            <Col md={4} key={index}>
              <div className="benefit-card">
                {item?.icon}
                <h5>{item?.title}</h5>
                <p>{item?.description}</p>
              </div>
            </Col>
          ))}
        </Row>

        {/* WHO IT’S FOR */}
        <Row className="mt-5">
          <Col>
            <h4>Who It’s For</h4>
            <p className="mt-3">
              DocRoute-RT is built for individuals who want a secure and reliable
              way to manage certificates, academic records, project files, and
              important paperwork — all in one place with full control.
            </p>
          </Col>
        </Row>

        {/* TECHNOLOGY STACK */}
        <Row className="mt-5 text-center">
          <Col>
            <h4>Powered By</h4>
            <div className="tech-badges mt-3">
              <span className="badge bg-dark me-2">FastAPI</span>
              <span className="badge bg-dark me-2">PostgreSQL</span>
              <span className="badge bg-dark me-2">React</span>
              <span className="badge bg-dark me-2">AI / NLP</span>
              <span className="badge bg-dark me-2">OCR</span>
              <span className="badge bg-dark me-2">JWT Security</span>
              <span className="badge bg-dark">QR Tracking</span>
            </div>
          </Col>
        </Row>

        {/* TAGLINE */}
        <Row className="mt-5 text-center">
          <Col>
            <p className="text-muted fw-semibold">
              Your documents. Your control.
            </p>
          </Col>
        </Row>

      </Container>
    </>
  );
}

export default About;
