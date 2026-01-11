import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";
import { AuthProvider } from "./context/AuthContext";
import { LanguageProvider } from "./context/LanguageContext";
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
import { PPSGuide, GNIBGuide, PassportGuide } from "./pages/Guides";

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <div className="App min-h-screen flex flex-col">
          <BrowserRouter>
            <Navbar />
            <main className="flex-1">
              <Routes>
                <Route path="/" element={<Landing />} />
                <Route path="/schools" element={<Schools />} />
                <Route path="/schools/:id" element={<SchoolDetail />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/payment/success" element={<PaymentSuccess />} />
                <Route path="/transport" element={<Transport />} />
                <Route path="/services" element={<Services />} />
                <Route path="/services/pps" element={<PPSGuide />} />
                <Route path="/services/gnib" element={<GNIBGuide />} />
                <Route path="/services/passport" element={<PassportGuide />} />
              </Routes>
            </main>
            <Footer />
          </BrowserRouter>
          <Toaster position="top-right" richColors />
        </div>
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;
