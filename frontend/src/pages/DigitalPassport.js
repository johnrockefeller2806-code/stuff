import { useState, useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLanguage } from "../context/LanguageContext";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { toast } from "sonner";
import { QRCodeSVG } from "qrcode.react";
import {
  User,
  GraduationCap,
  Building2,
  Calendar,
  Clock,
  MapPin,
  Phone,
  Mail,
  Globe,
  FileText,
  Download,
  QrCode,
  Shield,
  CheckCircle2,
  AlertCircle,
  ChevronLeft,
  ExternalLink,
  CreditCard,
  Loader2,
  Camera,
  Flag
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const DigitalPassport = () => {
  const { user, token } = useAuth();
  const { lang } = useLanguage();
  const navigate = useNavigate();
  const [passport, setPassport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState([]);
  const [activeTab, setActiveTab] = useState("passport");
  const passportRef = useRef(null);

  useEffect(() => {
    if (!user || !token) {
      navigate("/login");
      return;
    }
    fetchPassport();
  }, [user, token]);

  const fetchPassport = async () => {
    try {
      const response = await fetch(`${API}/passport/my`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setPassport(data);
        fetchDocuments(data.enrollment_id);
      } else {
        setPassport(null);
      }
    } catch (error) {
      console.error("Error fetching passport:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async (enrollmentId) => {
    try {
      const response = await fetch(`${API}/passport/documents/${enrollmentId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      }
    } catch (error) {
      console.error("Error fetching documents:", error);
    }
  };

  const getVerificationUrl = () => {
    if (!passport) return "";
    return `${window.location.origin}/passport/verify/${passport.qr_code_token}`;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "long",
      year: "numeric"
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "text-emerald-600 bg-emerald-50";
      case "inactive":
        return "text-yellow-600 bg-yellow-50";
      case "expired":
        return "text-red-600 bg-red-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getStatusText = (status) => {
    const texts = {
      active: { pt: "Ativo", en: "Active" },
      inactive: { pt: "Inativo", en: "Inactive" },
      expired: { pt: "Expirado", en: "Expired" }
    };
    return texts[status]?.[lang] || status;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  if (!passport) {
    return (
      <div className="min-h-screen bg-slate-50 py-12 px-4">
        <div className="max-w-2xl mx-auto text-center">
          <div className="bg-white rounded-3xl p-12 shadow-sm border border-slate-100">
            <div className="w-20 h-20 bg-amber-50 rounded-full flex items-center justify-center mx-auto mb-6">
              <CreditCard className="w-10 h-10 text-amber-600" />
            </div>
            <h1 className="font-serif text-3xl font-semibold text-slate-800 mb-4">
              {lang === "pt" ? "Passaporte Digital não encontrado" : "Digital Passport not found"}
            </h1>
            <p className="text-slate-600 mb-8 max-w-md mx-auto">
              {lang === "pt"
                ? "Seu passaporte digital será gerado automaticamente após o pagamento do curso. Complete sua matrícula para ter acesso."
                : "Your digital passport will be generated automatically after course payment. Complete your enrollment to access it."}
            </p>
            <div className="flex gap-4 justify-center">
              <Button
                onClick={() => navigate("/schools")}
                className="bg-emerald-700 hover:bg-emerald-800 text-white rounded-full px-8"
                data-testid="browse-schools-btn"
              >
                <GraduationCap className="w-4 h-4 mr-2" />
                {lang === "pt" ? "Ver Escolas" : "Browse Schools"}
              </Button>
              <Button
                onClick={() => navigate("/dashboard")}
                variant="outline"
                className="rounded-full px-8"
                data-testid="go-dashboard-btn"
              >
                {lang === "pt" ? "Meu Dashboard" : "My Dashboard"}
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-950 to-emerald-900">
      {/* Header */}
      <div className="bg-emerald-950/50 border-b border-emerald-800/30">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center text-emerald-200 hover:text-white transition-colors"
            data-testid="back-dashboard-btn"
          >
            <ChevronLeft className="w-5 h-5 mr-1" />
            {lang === "pt" ? "Voltar ao Dashboard" : "Back to Dashboard"}
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Page Title */}
        <div className="text-center mb-8">
          <h1 className="font-serif text-4xl md:text-5xl font-semibold text-white mb-2">
            {lang === "pt" ? "Passaporte Digital" : "Digital Passport"}
          </h1>
          <p className="text-emerald-200">
            {lang === "pt" ? "Identidade do Estudante Internacional" : "International Student Identity"}
          </p>
        </div>

        {/* Tabs */}
        <div className="flex justify-center gap-2 mb-8">
          {[
            { id: "passport", icon: CreditCard, label: { pt: "Passaporte", en: "Passport" } },
            { id: "documents", icon: FileText, label: { pt: "Documentos", en: "Documents" } },
            { id: "services", icon: ExternalLink, label: { pt: "Serviços", en: "Services" } }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-3 rounded-full font-medium transition-all ${
                activeTab === tab.id
                  ? "bg-white text-emerald-800"
                  : "bg-emerald-800/30 text-emerald-100 hover:bg-emerald-800/50"
              }`}
              data-testid={`tab-${tab.id}`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label[lang]}
            </button>
          ))}
        </div>

        {/* Passport Tab */}
        {activeTab === "passport" && (
          <div className="grid md:grid-cols-2 gap-8">
            {/* Passport Card */}
            <div ref={passportRef} className="bg-white rounded-3xl overflow-hidden shadow-2xl">
              {/* Header with gradient */}
              <div className="bg-gradient-to-r from-emerald-700 to-emerald-600 p-6 text-white">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                      <GraduationCap className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-emerald-100 text-sm">STUFF Intercâmbio</p>
                      <p className="font-semibold">Student Passport</p>
                    </div>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    passport.status === "active" ? "bg-emerald-500 text-white" : "bg-red-500 text-white"
                  }`}>
                    {getStatusText(passport.status)}
                  </div>
                </div>
                <div className="text-emerald-100 text-sm">
                  Nº {passport.enrollment_number}
                </div>
              </div>

              {/* Student Info */}
              <div className="p-6">
                <div className="flex items-start gap-4 mb-6">
                  {/* Photo */}
                  <div className="w-24 h-32 bg-slate-100 rounded-xl overflow-hidden flex-shrink-0 border-2 border-slate-200">
                    {passport.user_avatar ? (
                      <img
                        src={passport.user_avatar}
                        alt={passport.user_name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-emerald-50">
                        <User className="w-10 h-10 text-emerald-300" />
                      </div>
                    )}
                  </div>
                  
                  {/* Info */}
                  <div className="flex-1">
                    <h2 className="font-serif text-2xl font-semibold text-slate-800 mb-1">
                      {passport.user_name}
                    </h2>
                    <div className="flex items-center gap-2 text-slate-500 mb-3">
                      <Flag className="w-4 h-4" />
                      <span>{passport.user_nationality}</span>
                    </div>
                    <div className="space-y-1 text-sm text-slate-600">
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-slate-400" />
                        {passport.user_email}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Divider */}
                <div className="border-t border-dashed border-slate-200 my-6"></div>

                {/* School Info */}
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3">
                    {lang === "pt" ? "Escola" : "School"}
                  </h3>
                  <div className="flex items-center gap-3 mb-2">
                    <Building2 className="w-5 h-5 text-emerald-600" />
                    <span className="font-semibold text-slate-800">{passport.school_name}</span>
                  </div>
                  <div className="pl-8 space-y-1 text-sm text-slate-600">
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-slate-400" />
                      {passport.school_address}
                    </div>
                    {passport.school_phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-slate-400" />
                        {passport.school_phone}
                      </div>
                    )}
                    {passport.school_email && (
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-slate-400" />
                        {passport.school_email}
                      </div>
                    )}
                  </div>
                </div>

                {/* Course Info */}
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3">
                    {lang === "pt" ? "Curso" : "Course"}
                  </h3>
                  <div className="flex items-center gap-3 mb-2">
                    <GraduationCap className="w-5 h-5 text-emerald-600" />
                    <span className="font-semibold text-slate-800">{passport.course_name}</span>
                  </div>
                  <div className="pl-8 grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-slate-400">{lang === "pt" ? "Início" : "Start"}</p>
                      <p className="text-slate-700 font-medium">{formatDate(passport.course_start_date)}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">{lang === "pt" ? "Término" : "End"}</p>
                      <p className="text-slate-700 font-medium">{formatDate(passport.course_end_date)}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">{lang === "pt" ? "Duração" : "Duration"}</p>
                      <p className="text-slate-700 font-medium">{passport.course_duration_weeks} {lang === "pt" ? "semanas" : "weeks"}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">{lang === "pt" ? "Carga Horária" : "Schedule"}</p>
                      <p className="text-slate-700 font-medium">{passport.course_schedule}</p>
                    </div>
                  </div>
                </div>

                {/* Divider */}
                <div className="border-t border-dashed border-slate-200 my-6"></div>

                {/* Validity */}
                <div className="flex items-center justify-between text-sm">
                  <div>
                    <p className="text-slate-400">{lang === "pt" ? "Emitido em" : "Issued on"}</p>
                    <p className="text-slate-700 font-medium">{formatDate(passport.issued_at)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-slate-400">{lang === "pt" ? "Válido até" : "Valid until"}</p>
                    <p className="text-slate-700 font-medium">{formatDate(passport.valid_until)}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* QR Code & Actions */}
            <div className="space-y-6">
              {/* QR Code Card */}
              <Card className="bg-white rounded-3xl shadow-lg border-0">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-slate-800">
                    <QrCode className="w-5 h-5 text-emerald-600" />
                    {lang === "pt" ? "QR Code de Verificação" : "Verification QR Code"}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col items-center">
                    <div className="bg-white p-4 rounded-2xl border-2 border-slate-100 mb-4">
                      <QRCodeSVG
                        value={getVerificationUrl()}
                        size={180}
                        level="H"
                        includeMargin={true}
                        data-testid="passport-qrcode"
                      />
                    </div>
                    <p className="text-sm text-slate-500 text-center mb-4">
                      {lang === "pt"
                        ? "Escaneie para verificar a autenticidade do passaporte"
                        : "Scan to verify passport authenticity"}
                    </p>
                    <div className="flex items-center gap-2 text-emerald-600 bg-emerald-50 px-4 py-2 rounded-full">
                      <Shield className="w-4 h-4" />
                      <span className="text-sm font-medium">
                        {lang === "pt" ? "Verificação Segura" : "Secure Verification"}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Info Card */}
              <Card className="bg-emerald-50 rounded-3xl shadow-sm border-emerald-100">
                <CardContent className="pt-6">
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-emerald-800 mb-1">
                        {lang === "pt" ? "Passaporte Verificado" : "Verified Passport"}
                      </h4>
                      <p className="text-sm text-emerald-700">
                        {lang === "pt"
                          ? "Este passaporte digital é um documento oficial emitido pela STUFF Intercâmbio e pode ser verificado por qualquer pessoa através do QR Code."
                          : "This digital passport is an official document issued by STUFF Intercâmbio and can be verified by anyone through the QR Code."}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Tip to add photo */}
              {!passport.user_avatar && (
                <Card className="bg-amber-50 rounded-3xl shadow-sm border-amber-100">
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-3">
                      <Camera className="w-5 h-5 text-amber-600 mt-0.5" />
                      <div>
                        <h4 className="font-semibold text-amber-800 mb-1">
                          {lang === "pt" ? "Adicione sua foto" : "Add your photo"}
                        </h4>
                        <p className="text-sm text-amber-700 mb-3">
                          {lang === "pt"
                            ? "Seu passaporte ficará mais completo com uma foto. Adicione no seu perfil."
                            : "Your passport will be more complete with a photo. Add it in your profile."}
                        </p>
                        <Button
                          onClick={() => navigate("/profile")}
                          size="sm"
                          className="bg-amber-600 hover:bg-amber-700 text-white rounded-full"
                          data-testid="add-photo-btn"
                        >
                          <Camera className="w-4 h-4 mr-2" />
                          {lang === "pt" ? "Adicionar Foto" : "Add Photo"}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}

        {/* Documents Tab */}
        {activeTab === "documents" && (
          <div className="max-w-3xl mx-auto">
            <Card className="bg-white rounded-3xl shadow-lg border-0">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-800">
                  <FileText className="w-5 h-5 text-emerald-600" />
                  {lang === "pt" ? "Meus Documentos" : "My Documents"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {documents.map((doc) => (
                    <div
                      key={doc.id}
                      className={`flex items-center justify-between p-4 rounded-2xl border ${
                        doc.available ? "border-slate-200 bg-white" : "border-slate-100 bg-slate-50"
                      }`}
                      data-testid={`document-${doc.id}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                          doc.available ? "bg-emerald-50" : "bg-slate-100"
                        }`}>
                          <FileText className={`w-5 h-5 ${
                            doc.available ? "text-emerald-600" : "text-slate-400"
                          }`} />
                        </div>
                        <div>
                          <p className={`font-medium ${doc.available ? "text-slate-800" : "text-slate-500"}`}>
                            {lang === "pt" ? doc.name : doc.name_en}
                          </p>
                          <p className="text-sm text-slate-400">
                            {doc.type === "auto_generated" 
                              ? (lang === "pt" ? "Gerado automaticamente" : "Auto-generated")
                              : (lang === "pt" ? "Enviado pela escola" : "Uploaded by school")}
                          </p>
                        </div>
                      </div>
                      {doc.available ? (
                        doc.url ? (
                          <a
                            href={doc.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-full text-sm font-medium transition-colors"
                          >
                            <ExternalLink className="w-4 h-4" />
                            {lang === "pt" ? "Abrir" : "Open"}
                          </a>
                        ) : (
                          <span className="flex items-center gap-2 text-emerald-600 bg-emerald-50 px-4 py-2 rounded-full text-sm font-medium">
                            <CheckCircle2 className="w-4 h-4" />
                            {lang === "pt" ? "Disponível" : "Available"}
                          </span>
                        )
                      ) : (
                        <span className="flex items-center gap-2 text-slate-400 bg-slate-100 px-4 py-2 rounded-full text-sm">
                          <Clock className="w-4 h-4" />
                          {lang === "pt" ? "Pendente" : "Pending"}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Services Tab */}
        {activeTab === "services" && (
          <div className="max-w-3xl mx-auto">
            <Card className="bg-white rounded-3xl shadow-lg border-0">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-800">
                  <ExternalLink className="w-5 h-5 text-emerald-600" />
                  {lang === "pt" ? "Serviços Úteis" : "Useful Services"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600 mb-6">
                  {lang === "pt"
                    ? "Links importantes para estudantes internacionais na Irlanda"
                    : "Important links for international students in Ireland"}
                </p>
                <div className="space-y-4">
                  {[
                    {
                      id: "pps",
                      title: "PPS Number",
                      description: {
                        pt: "Solicitar número PPS para trabalhar na Irlanda",
                        en: "Apply for PPS number to work in Ireland"
                      },
                      url: "https://www.mywelfare.ie",
                      checklist: [
                        { pt: "Passaporte válido", en: "Valid passport" },
                        { pt: "Carta da escola", en: "School letter" },
                        { pt: "Comprovante de endereço", en: "Proof of address" }
                      ]
                    },
                    {
                      id: "gnib",
                      title: "GNIB/IRP",
                      description: {
                        pt: "Agendar registro de imigração",
                        en: "Schedule immigration registration"
                      },
                      url: "https://burghquayregistrationoffice.inis.gov.ie/",
                      checklist: [
                        { pt: "Passaporte válido", en: "Valid passport" },
                        { pt: "Comprovante financeiro (€4.200)", en: "Proof of funds (€4,200)" },
                        { pt: "Seguro saúde", en: "Health insurance" },
                        { pt: "Taxa de €300", en: "€300 fee" }
                      ]
                    },
                    {
                      id: "ndls",
                      title: lang === "pt" ? "Carteira de Motorista" : "Driver's License",
                      description: {
                        pt: "Solicitar carteira de motorista irlandesa",
                        en: "Apply for Irish driver's license"
                      },
                      url: "https://www.ndls.ie",
                      checklist: [
                        { pt: "Theory Test aprovado", en: "Theory Test passed" },
                        { pt: "12 aulas EDT", en: "12 EDT lessons" },
                        { pt: "Learner Permit", en: "Learner Permit" }
                      ]
                    },
                    {
                      id: "revenue",
                      title: "Revenue",
                      description: {
                        pt: "Registrar para impostos e obter tax credit",
                        en: "Register for taxes and get tax credit"
                      },
                      url: "https://www.revenue.ie",
                      checklist: [
                        { pt: "PPS Number", en: "PPS Number" },
                        { pt: "Emprego ativo", en: "Active employment" }
                      ]
                    }
                  ].map((service) => (
                    <div
                      key={service.id}
                      className="p-5 rounded-2xl border border-slate-200 hover:border-emerald-200 hover:bg-emerald-50/30 transition-all"
                      data-testid={`service-${service.id}`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-slate-800">{service.title}</h4>
                          <p className="text-sm text-slate-600">{service.description[lang]}</p>
                        </div>
                        <a
                          href={service.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-full text-sm font-medium transition-colors"
                        >
                          <ExternalLink className="w-4 h-4" />
                          {lang === "pt" ? "Acessar" : "Access"}
                        </a>
                      </div>
                      <div className="mt-3 pt-3 border-t border-slate-100">
                        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
                          {lang === "pt" ? "Documentos necessários" : "Required documents"}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {service.checklist.map((item, idx) => (
                            <span
                              key={idx}
                              className="text-xs bg-slate-100 text-slate-600 px-3 py-1 rounded-full"
                            >
                              {item[lang]}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

// Public verification page
export const PassportVerify = () => {
  const { token } = useParams();
  const { lang } = useLanguage();
  const [passport, setPassport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPassportVerification();
  }, [token]);

  const fetchPassportVerification = async () => {
    try {
      const response = await fetch(`${API}/passport/verify/${token}`);
      if (response.ok) {
        const data = await response.json();
        setPassport(data);
      } else {
        setError(lang === "pt" ? "Passaporte não encontrado" : "Passport not found");
      }
    } catch (error) {
      setError(lang === "pt" ? "Erro ao verificar passaporte" : "Error verifying passport");
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "long",
      year: "numeric"
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full bg-white rounded-3xl shadow-lg border-0">
          <CardContent className="pt-8 pb-8 text-center">
            <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
            <h2 className="font-serif text-2xl font-semibold text-slate-800 mb-2">
              {lang === "pt" ? "Verificação Falhou" : "Verification Failed"}
            </h2>
            <p className="text-slate-600">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-950 to-emerald-900 flex items-center justify-center p-4">
      <Card className="max-w-lg w-full bg-white rounded-3xl shadow-2xl border-0 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-600 to-emerald-500 p-6 text-white text-center">
          <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-3">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="font-serif text-2xl font-semibold mb-1">
            {lang === "pt" ? "Passaporte Verificado" : "Passport Verified"}
          </h1>
          <p className="text-emerald-100 text-sm">STUFF Intercâmbio</p>
        </div>

        <CardContent className="p-6">
          {/* Status */}
          <div className="flex items-center justify-center mb-6">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${
              passport.status === "active" 
                ? "bg-emerald-50 text-emerald-700" 
                : "bg-red-50 text-red-700"
            }`}>
              {passport.status === "active" ? (
                <CheckCircle2 className="w-5 h-5" />
              ) : (
                <AlertCircle className="w-5 h-5" />
              )}
              <span className="font-semibold">
                {passport.status === "active" 
                  ? (lang === "pt" ? "Matrícula Ativa" : "Active Enrollment")
                  : (lang === "pt" ? "Matrícula Inativa" : "Inactive Enrollment")}
              </span>
            </div>
          </div>

          {/* Student Info */}
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-2xl">
              <User className="w-5 h-5 text-emerald-600" />
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wider">
                  {lang === "pt" ? "Estudante" : "Student"}
                </p>
                <p className="font-semibold text-slate-800">{passport.student_name}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-2xl">
              <Flag className="w-5 h-5 text-emerald-600" />
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wider">
                  {lang === "pt" ? "Nacionalidade" : "Nationality"}
                </p>
                <p className="font-semibold text-slate-800">{passport.student_nationality}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-2xl">
              <CreditCard className="w-5 h-5 text-emerald-600" />
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wider">
                  {lang === "pt" ? "Nº Matrícula" : "Enrollment Nº"}
                </p>
                <p className="font-semibold text-slate-800">{passport.enrollment_number}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-2xl">
              <Building2 className="w-5 h-5 text-emerald-600" />
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wider">
                  {lang === "pt" ? "Escola" : "School"}
                </p>
                <p className="font-semibold text-slate-800">{passport.school_name}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-2xl">
              <GraduationCap className="w-5 h-5 text-emerald-600" />
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wider">
                  {lang === "pt" ? "Curso" : "Course"}
                </p>
                <p className="font-semibold text-slate-800">{passport.course_name}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 rounded-2xl">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                  {lang === "pt" ? "Início" : "Start"}
                </p>
                <p className="font-semibold text-slate-800 text-sm">{formatDate(passport.course_start_date)}</p>
              </div>
              <div className="p-4 bg-slate-50 rounded-2xl">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                  {lang === "pt" ? "Término" : "End"}
                </p>
                <p className="font-semibold text-slate-800 text-sm">{formatDate(passport.course_end_date)}</p>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-6 pt-6 border-t border-slate-100 text-center">
            <p className="text-xs text-slate-400">
              {lang === "pt" ? "Emitido em" : "Issued on"} {formatDate(passport.issued_at)}
            </p>
            <p className="text-xs text-slate-400">
              {lang === "pt" ? "Válido até" : "Valid until"} {formatDate(passport.valid_until)}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
