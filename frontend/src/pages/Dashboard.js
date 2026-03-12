import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import { 
  GraduationCap, 
  Calendar, 
  CreditCard,
  CheckCircle,
  Clock,
  AlertCircle,
  ArrowRight,
  BookOpen,
  IdCard
} from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const Dashboard = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const { t, language } = useLanguage();
  
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingPayment, setProcessingPayment] = useState(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login');
      return;
    }
    if (isAuthenticated) {
      fetchEnrollments();
    }
  }, [isAuthenticated, authLoading]);

  const fetchEnrollments = async () => {
    try {
      const response = await axios.get(`${API}/enrollments`);
      setEnrollments(response.data);
    } catch (error) {
      console.error('Error fetching enrollments:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async (enrollment) => {
    setProcessingPayment(enrollment.id);
    try {
      const response = await axios.post(`${API}/payments/checkout`, {
        enrollment_id: enrollment.id,
        origin_url: window.location.origin
      });
      
      if (response.data.url) {
        window.location.href = response.data.url;
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Error creating payment');
    } finally {
      setProcessingPayment(null);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: {
        label: t('dashboard_status_pending'),
        className: 'bg-amber-100 text-amber-800',
        icon: Clock
      },
      paid: {
        label: t('dashboard_status_paid'),
        className: 'bg-emerald-100 text-emerald-800',
        icon: CheckCircle
      },
      confirmed: {
        label: t('dashboard_status_confirmed'),
        className: 'bg-blue-100 text-blue-800',
        icon: CheckCircle
      },
      cancelled: {
        label: language === 'pt' ? 'Cancelado' : 'Cancelled',
        className: 'bg-red-100 text-red-800',
        icon: AlertCircle
      }
    };
    
    const config = statusConfig[status] || statusConfig.pending;
    const Icon = config.icon;
    
    return (
      <Badge className={`${config.className} gap-1`}>
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-slate-50 py-12" data-testid="dashboard-loading">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <Skeleton className="h-12 w-64 mb-8" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Skeleton className="h-32 rounded-xl" />
            <Skeleton className="h-32 rounded-xl" />
            <Skeleton className="h-32 rounded-xl" />
          </div>
          <Skeleton className="h-64 rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="dashboard-page">
      {/* Header */}
      <div className="bg-emerald-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <h1 className="font-serif text-3xl md:text-4xl font-bold mb-2" data-testid="dashboard-title">
            {language === 'pt' ? `Olá, ${user?.name?.split(' ')[0]}!` : `Hello, ${user?.name?.split(' ')[0]}!`}
          </h1>
          <p className="text-emerald-200">
            {language === 'pt' ? 'Gerencie suas matrículas e pagamentos' : 'Manage your enrollments and payments'}
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 -mt-12 mb-8">
          <Card className="border-slate-100 shadow-lg" data-testid="stat-enrollments">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="p-3 bg-emerald-100 rounded-xl">
                <GraduationCap className="h-6 w-6 text-emerald-700" />
              </div>
              <div>
                <p className="text-sm text-slate-500">{t('dashboard_enrollments')}</p>
                <p className="text-2xl font-bold text-slate-900">{enrollments.length}</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-slate-100 shadow-lg" data-testid="stat-pending">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="p-3 bg-amber-100 rounded-xl">
                <Clock className="h-6 w-6 text-amber-700" />
              </div>
              <div>
                <p className="text-sm text-slate-500">{language === 'pt' ? 'Pendentes' : 'Pending'}</p>
                <p className="text-2xl font-bold text-slate-900">
                  {enrollments.filter(e => e.status === 'pending').length}
                </p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-slate-100 shadow-lg" data-testid="stat-paid">
            <CardContent className="p-6 flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-xl">
                <CreditCard className="h-6 w-6 text-blue-700" />
              </div>
              <div>
                <p className="text-sm text-slate-500">{language === 'pt' ? 'Pagos' : 'Paid'}</p>
                <p className="text-2xl font-bold text-slate-900">
                  {enrollments.filter(e => e.status === 'paid' || e.status === 'confirmed').length}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Enrollments List */}
        <Card className="border-slate-100" data-testid="enrollments-card">
          <CardHeader>
            <CardTitle className="font-serif flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              {t('dashboard_enrollments')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {enrollments.length === 0 ? (
              <div className="text-center py-12" data-testid="no-enrollments">
                <GraduationCap className="h-12 w-12 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-500 mb-4">{t('dashboard_no_enrollments')}</p>
                <Link to="/schools">
                  <Button className="bg-emerald-900 hover:bg-emerald-800">
                    {t('hero_cta')}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {enrollments.map((enrollment) => (
                  <div 
                    key={enrollment.id}
                    className="border border-slate-100 rounded-xl p-4 md:p-6 hover:bg-slate-50 transition-colors"
                    data-testid={`enrollment-${enrollment.id}`}
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold text-slate-900">{enrollment.course_name}</h3>
                          {getStatusBadge(enrollment.status)}
                        </div>
                        <p className="text-slate-500 text-sm mb-2">{enrollment.school_name}</p>
                        <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            {language === 'pt' ? 'Início:' : 'Start:'} {new Date(enrollment.start_date).toLocaleDateString()}
                          </div>
                          <div className="flex items-center gap-1">
                            <CreditCard className="h-4 w-4" />
                            €{enrollment.price.toLocaleString()}
                          </div>
                        </div>
                      </div>
                      
                      {enrollment.status === 'pending' && (
                        <Button 
                          onClick={() => handlePayment(enrollment)}
                          disabled={processingPayment === enrollment.id}
                          className="bg-amber-600 hover:bg-amber-500"
                          data-testid={`pay-button-${enrollment.id}`}
                        >
                          {processingPayment === enrollment.id ? t('loading') : t('dashboard_pay_now')}
                        </Button>
                      )}
                      
                      {enrollment.status === 'paid' && (
                        <div className="flex items-center gap-3">
                          <Button 
                            onClick={() => navigate('/passport')}
                            className="bg-emerald-700 hover:bg-emerald-600"
                            data-testid={`passport-button-${enrollment.id}`}
                          >
                            <IdCard className="h-4 w-4 mr-2" />
                            {language === 'pt' ? 'Passaporte Digital' : 'Digital Passport'}
                          </Button>
                          <div className="text-right">
                            <p className="text-sm text-emerald-600 font-medium">
                              {language === 'pt' ? 'Carta em processamento' : 'Letter in process'}
                            </p>
                            <p className="text-xs text-slate-400">
                              {language === 'pt' ? 'Até 5 dias úteis' : 'Up to 5 business days'}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
