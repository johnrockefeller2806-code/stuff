import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { AuthProvider } from "./context/AuthContext";
import { LanguageProvider } from "./context/LanguageContext";
import { AuthCallback } from "./components/AuthCallback";
import { Navbar } from "./components/Navbar";
import { Footer } from "./components/Footer";
import { Landing } from "./pages/Landing";
import { Schools } from "./pages/Schools";
import { SchoolDetail } from "./pages/SchoolDetail";
import { Login, Register } from "./pages/Auth";
import { Dashboard } from "./pages/Dashboard";
import { PaymentSuccess } from "./pages/PaymentSuccess";
import { Transport } from "./pages/Transport";
import { Services } from "./pages/Services";
import { PPSGuide, GNIBGuide, PassportGuide, DrivingLicenseGuide } from "./pages/Guides";
import { AdminDashboard } from "./pages/AdminDashboard";
import { SchoolDashboard } from "./pages/SchoolDashboard";
import { SchoolRegister } from "./pages/SchoolRegister";
import { SchoolSubscription } from "./pages/SchoolSubscription";
import { StuffDuvidas } from "./pages/StuffDuvidas";
import { StudentGuide } from "./pages/StudentGuide";
import { About } from "./pages/About";
import { Flights } from "./pages/Flights";
import { Insurance } from "./pages/Insurance";
import { Chat } from "./pages/Chat";
import { Profile } from "./pages/Profile";
import { PlusPaywall } from "./pages/PlusPaywall";
import { PlusSuccess } from "./pages/PlusSuccess";
import { Tourism } from "./pages/Tourism";
import { Emergency } from "./pages/Emergency";
import { DigitalPassport, PassportVerify } from "./pages/DigitalPassport";
import { PassportView } from "./pages/PassportView";
import { ContractSign } from "./pages/ContractSign";
import { EnrollmentTracker } from "./pages/EnrollmentTracker";
import { DestinoAI } from "./pages/DestinoAI";

// Layout component to conditionally show navbar/footer
const AppLayout = ({ children }) => {
  const location = useLocation();
  const isChat = location.pathname === '/chat';
  const isPassportView = location.pathname.startsWith('/passport/view/');
  const isDestinoAI = location.pathname === '/destinoai';
  const hideNavFooter = isChat || isPassportView || isDestinoAI;
  
  return (
    <div className={`App ${hideNavFooter ? '' : 'min-h-screen flex flex-col'}`}>
      {!hideNavFooter && <Navbar />}
      <main className={hideNavFooter ? '' : 'flex-1'}>
        {children}
      </main>
      {!hideNavFooter && <Footer />}
    </div>
  );
};

// Router component that handles session_id detection
const AppRouter = () => {
  const location = useLocation();
  
  // CRITICAL: Check URL fragment (not query params) for session_id
  // This must be synchronous during render to prevent race conditions
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }
  
  return (
    <AppLayout>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Landing />} />
        <Route path="/destinoai" element={<DestinoAI />} />
        <Route path="/schools" element={<Schools />} />
        <Route path="/schools/:id" element={<SchoolDetail />} />
        <Route path="/transport" element={<Transport />} />
        <Route path="/tourism" element={<Tourism />} />
        <Route path="/emergency" element={<Emergency />} />
        <Route path="/services" element={<Services />} />
        <Route path="/services/pps" element={<PPSGuide />} />
        <Route path="/services/gnib" element={<GNIBGuide />} />
        <Route path="/services/passport" element={<PassportGuide />} />
        <Route path="/services/driving-license" element={<DrivingLicenseGuide />} />
        <Route path="/duvidas" element={<StuffDuvidas />} />
        <Route path="/guia-estudante" element={<StudentGuide />} />
        <Route path="/sobre" element={<About />} />
        <Route path="/passagens" element={<Flights />} />
        <Route path="/seguro" element={<Insurance />} />
        <Route path="/chat" element={<Chat />} />
        
        {/* Auth Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/register-school" element={<SchoolRegister />} />
        
        {/* User Routes */}
        <Route path="/profile" element={<Profile />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/payment/success" element={<PaymentSuccess />} />
        <Route path="/passport" element={<DigitalPassport />} />
        <Route path="/passport/verify/:token" element={<PassportVerify />} />
        <Route path="/passport/view/:token" element={<PassportView />} />
        <Route path="/contract/:enrollmentId" element={<ContractSign />} />
        <Route path="/enrollment/:enrollmentId" element={<EnrollmentTracker />} />
        
        {/* PLUS Plan Routes */}
        <Route path="/plus" element={<PlusPaywall />} />
        <Route path="/plus/success" element={<PlusSuccess />} />
        
        {/* Admin Routes */}
        <Route path="/admin" element={<AdminDashboard />} />
        
        {/* School Routes */}
        <Route path="/school" element={<SchoolDashboard />} />
        <Route path="/school/subscription" element={<SchoolSubscription />} />
        <Route path="/school/subscription/success" element={<SchoolSubscription />} />
      </Routes>
    </AppLayout>
  );
};

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppRouter />
          <Toaster position="top-right" richColors />
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
