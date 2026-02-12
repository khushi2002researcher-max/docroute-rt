import { BrowserRouter, Routes, Route } from "react-router-dom";

// Pages
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import OCRDigitization from "./pages/OCRDigitization";
import AISummarization from "./pages/AISummarization";
import DocumentTracking from "./pages/DocumentTracking";
import QRTracking from "./pages/QRTracking";
import Analytics from "./pages/Analytics";
import ShareDocumentView from "./pages/ShareDocumentView"; // ✅ ADD THIS
import QRDetails from "./pages/QRDetails";
import AIworkflow from "./pages/AIwordkflow";
import DocCodeExchange from "./pages/DocCodeExchange";
import Profile from "./pages/Profile"
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";




// Dashboard Layout
import DashboardLayout from "./layouts/DashboardLayout";
import About from "./pages/About";
// Route protection
import ProtectedRoute from "./routes/ProtectedRoute";

function App() {
  return (
    <BrowserRouter>
      <Routes>
       {/* Public Routes */}
<Route path="/" element={<Home />} />
<Route path="/login" element={<Login />} />
<Route path="/register" element={<Register />} />

{/* 🔑 Forgot / Reset Password */}
<Route path="/forgot-password" element={<ForgotPassword />} />
<Route path="/reset-password/:token" element={<ResetPassword />} />


        {/* 📄 Document Tracking QR */}
<Route path="/share/doc/:token" element={<ShareDocumentView />} />

{/* 📦 Physical Document QR */}
<Route path="/share/physical/:token" element={<QRDetails />} />

<Route path="/about" element={<About />} />




        {/* 🔐 Protected Dashboard Routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Analytics />} />

<Route path="analytics" element={<Analytics />} />
<Route path="doc-code" element={<DocCodeExchange />} />
<Route path="profile" element={<Profile />} />


<Route path="ocr" element={<OCRDigitization />} />
<Route path="ai-summary" element={<AISummarization />} />
<Route path="tracking" element={<DocumentTracking />} />
<Route path="qr" element={<QRTracking />} />
<Route path="aiworkflow" element={<AIworkflow />} />

        </Route>

        {/* 404 fallback */}
        <Route
          path="*"
          element={<h2 className="text-center mt-5">404 - Page Not Found</h2>}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
