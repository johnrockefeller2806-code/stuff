import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { 
  Check, 
  Crown, 
  Star, 
  Zap,
  ArrowRight,
  Loader2,
  CheckCircle,
  Building2,
  TrendingUp,
  Euro
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const LOGO_URL = "https://customer-assets.emergentagent.com/job_dublin-study/artifacts/o9gnc0xi_WhatsApp%20Image%202026-01-11%20at%2023.59.07.jpeg";

export const SchoolSubscription = () => {
  const { token, user } = useAuth();
  const { language } = useLanguage();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [plans, setPlans] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [subscribing, setSubscribing] = useState(null);
  const [checkingPayment, setCheckingPayment] = useState(false);

  // Plan icons and colors
  const planStyles = {
    starter: { 
      icon: Zap, 
      color: 'text-blue-600', 
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      buttonColor: 'bg-blue-600 hover:bg-blue-500'
    },
    professional: { 
      icon: Star, 
      color: 'text-amber-600', 
      bgColor: 'bg-amber-50',
      borderColor: 'border-amber-200',
      buttonColor: 'bg-amber-600 hover:bg-amber-500',
      popular: true
    },
    premium: { 
      icon: Crown, 
      color: 'text-purple-600', 
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
      buttonColor: 'bg-purple-600 hover:bg-purple-500'
    }
  };

  // Load plans and current subscription
  const loadData = useCallback(async () => {
    try {
      const [plansRes, subRes] = await Promise.all([
        fetch(`${API_URL}/api/school/subscription/plans`),
        fetch(`${API_URL}/api/school/subscription`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);
      
      if (plansRes.ok) {
        const plansData = await plansRes.json();
        setPlans(plansData.plans);
      }
      
      if (subRes.ok) {
        const subData = await subRes.json();
        setCurrentSubscription(subData);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Check payment status if returning from Stripe
  const checkPaymentStatus = useCallback(async (sessionId) => {
    setCheckingPayment(true);
    let attempts = 0;
    const maxAttempts = 5;
    
    const poll = async () => {
      try {
        const response = await fetch(
          `${API_URL}/api/school/subscription/status/${sessionId}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        
        if (response.ok) {
          const data = await response.json();
          
          if (data.payment_status === 'paid') {
            toast.success(language === 'pt' 
              ? 'Assinatura ativada com sucesso!' 
              : 'Subscription activated successfully!');
            setCheckingPayment(false);
            loadData();
            // Clear URL params
            navigate('/school/subscription', { replace: true });
            return;
          }
        }
        
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        } else {
          setCheckingPayment(false);
          toast.error(language === 'pt' 
            ? 'Não foi possível verificar o pagamento. Tente novamente.' 
            : 'Could not verify payment. Please try again.');
        }
      } catch (error) {
        console.error('Error checking payment:', error);
        setCheckingPayment(false);
      }
    };
    
    poll();
  }, [token, language, loadData, navigate]);

  useEffect(() => {
    loadData();
    
    // Check if returning from Stripe
    const sessionId = searchParams.get('session_id');
    if (sessionId) {
      checkPaymentStatus(sessionId);
    }
  }, [loadData, searchParams, checkPaymentStatus]);

  // Subscribe to a plan
  const subscribeToPlan = async (planId) => {
    setSubscribing(planId);
    
    try {
      const response = await fetch(`${API_URL}/api/school/subscription/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          plan: planId,
          origin_url: window.location.origin
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        // Redirect to Stripe checkout
        window.location.href = data.checkout_url;
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Erro ao processar assinatura');
      }
    } catch (error) {
      console.error('Error subscribing:', error);
      toast.error(language === 'pt' ? 'Erro ao processar assinatura' : 'Error processing subscription');
    } finally {
      setSubscribing(null);
    }
  };

  if (loading || checkingPayment) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-emerald-600 mx-auto mb-4" />
          <p className="text-slate-600">
            {checkingPayment 
              ? (language === 'pt' ? 'Verificando pagamento...' : 'Verifying payment...')
              : (language === 'pt' ? 'Carregando...' : 'Loading...')
            }
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="subscription-page">
      {/* Header */}
      <div className="bg-gradient-to-br from-emerald-900 to-emerald-800 text-white py-12">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <div className="flex items-center gap-4 mb-4">
            <img 
              src={LOGO_URL} 
              alt="STUFF Intercâmbio" 
              className="h-12 w-auto bg-white rounded-lg p-1"
            />
          </div>
          <h1 className="font-serif text-3xl md:text-4xl font-bold mb-2">
            {language === 'pt' ? 'Planos para Escolas' : 'School Plans'}
          </h1>
          <p className="text-emerald-200 text-lg">
            {language === 'pt' 
              ? 'Escolha o plano ideal para sua escola e comece a receber alunos'
              : 'Choose the ideal plan for your school and start receiving students'}
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-12">
        {/* Current Subscription Status */}
        {currentSubscription && currentSubscription.status === 'active' && (
          <Card className="mb-8 border-emerald-200 bg-emerald-50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-emerald-100 rounded-full">
                    <CheckCircle className="h-6 w-6 text-emerald-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-emerald-900">
                      {language === 'pt' ? 'Plano Ativo' : 'Active Plan'}: {currentSubscription.plan_details?.name}
                    </h3>
                    <p className="text-emerald-700 text-sm">
                      {language === 'pt' ? 'Comissão' : 'Commission'}: {currentSubscription.plan_details?.commission_rate}%
                    </p>
                  </div>
                </div>
                <Button 
                  variant="outline" 
                  className="border-emerald-300 text-emerald-700"
                  onClick={() => navigate('/school')}
                >
                  <TrendingUp className="h-4 w-4 mr-2" />
                  {language === 'pt' ? 'Ver Dashboard' : 'View Dashboard'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Plans Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan) => {
            const style = planStyles[plan.id] || planStyles.starter;
            const Icon = style.icon;
            const isCurrentPlan = currentSubscription?.plan === plan.id && currentSubscription?.status === 'active';
            
            return (
              <Card 
                key={plan.id}
                className={`relative overflow-hidden transition-all hover:shadow-lg ${
                  style.popular ? 'ring-2 ring-amber-400 shadow-lg' : ''
                } ${isCurrentPlan ? 'ring-2 ring-emerald-400' : ''}`}
                data-testid={`plan-${plan.id}`}
              >
                {/* Popular Badge */}
                {style.popular && (
                  <div className="absolute top-0 right-0 bg-amber-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
                    {language === 'pt' ? 'POPULAR' : 'POPULAR'}
                  </div>
                )}
                
                {/* Current Plan Badge */}
                {isCurrentPlan && (
                  <div className="absolute top-0 left-0 bg-emerald-500 text-white text-xs font-bold px-3 py-1 rounded-br-lg">
                    {language === 'pt' ? 'SEU PLANO' : 'YOUR PLAN'}
                  </div>
                )}
                
                <CardHeader className={`${style.bgColor} border-b ${style.borderColor}`}>
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`p-2 rounded-lg ${style.bgColor}`}>
                      <Icon className={`h-6 w-6 ${style.color}`} />
                    </div>
                    <CardTitle className="text-xl">{plan.name}</CardTitle>
                  </div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-bold text-slate-900">€{plan.price}</span>
                    <span className="text-slate-500">/mês</span>
                  </div>
                  <CardDescription className="mt-2">{plan.description}</CardDescription>
                </CardHeader>
                
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    {/* Commission Rate */}
                    <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                      <Euro className={`h-5 w-5 ${style.color}`} />
                      <div>
                        <p className="font-medium text-slate-900">
                          {language === 'pt' ? 'Comissão por matrícula' : 'Commission per enrollment'}
                        </p>
                        <p className={`text-2xl font-bold ${style.color}`}>{plan.commission_rate}%</p>
                      </div>
                    </div>
                    
                    {/* Features */}
                    <ul className="space-y-3">
                      {[
                        language === 'pt' ? 'Listagem na plataforma' : 'Platform listing',
                        language === 'pt' ? 'Gestão de cursos' : 'Course management',
                        language === 'pt' ? 'Dashboard de vendas' : 'Sales dashboard',
                        language === 'pt' ? 'Envio de cartas' : 'Letter sending',
                        language === 'pt' ? 'Suporte por email' : 'Email support'
                      ].map((feature, index) => (
                        <li key={index} className="flex items-center gap-2">
                          <Check className={`h-4 w-4 ${style.color}`} />
                          <span className="text-slate-600">{feature}</span>
                        </li>
                      ))}
                      {plan.id === 'professional' && (
                        <li className="flex items-center gap-2">
                          <Check className={`h-4 w-4 ${style.color}`} />
                          <span className="text-slate-600">
                            {language === 'pt' ? 'Destaque na busca' : 'Search highlight'}
                          </span>
                        </li>
                      )}
                      {plan.id === 'premium' && (
                        <>
                          <li className="flex items-center gap-2">
                            <Check className={`h-4 w-4 ${style.color}`} />
                            <span className="text-slate-600">
                              {language === 'pt' ? 'Destaque na busca' : 'Search highlight'}
                            </span>
                          </li>
                          <li className="flex items-center gap-2">
                            <Check className={`h-4 w-4 ${style.color}`} />
                            <span className="text-slate-600">
                              {language === 'pt' ? 'Suporte prioritário' : 'Priority support'}
                            </span>
                          </li>
                        </>
                      )}
                    </ul>
                  </div>
                </CardContent>
                
                <CardFooter className="pt-0">
                  <Button
                    className={`w-full ${style.buttonColor} text-white`}
                    onClick={() => subscribeToPlan(plan.id)}
                    disabled={isCurrentPlan || subscribing === plan.id}
                    data-testid={`subscribe-${plan.id}`}
                  >
                    {subscribing === plan.id ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        {language === 'pt' ? 'Processando...' : 'Processing...'}
                      </>
                    ) : isCurrentPlan ? (
                      <>
                        <CheckCircle className="h-4 w-4 mr-2" />
                        {language === 'pt' ? 'Plano Atual' : 'Current Plan'}
                      </>
                    ) : (
                      <>
                        {language === 'pt' ? 'Assinar Plano' : 'Subscribe'}
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </>
                    )}
                  </Button>
                </CardFooter>
              </Card>
            );
          })}
        </div>

        {/* FAQ Section */}
        <div className="mt-16">
          <h2 className="font-serif text-2xl font-bold text-slate-900 mb-6 text-center">
            {language === 'pt' ? 'Perguntas Frequentes' : 'Frequently Asked Questions'}
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold text-slate-900 mb-2">
                  {language === 'pt' ? 'Como funciona a comissão?' : 'How does the commission work?'}
                </h3>
                <p className="text-slate-600 text-sm">
                  {language === 'pt' 
                    ? 'A comissão é automaticamente deduzida de cada matrícula. Por exemplo, se um curso custa €1000 e sua comissão é 5%, você recebe €950.'
                    : 'The commission is automatically deducted from each enrollment. For example, if a course costs €1000 and your commission is 5%, you receive €950.'}
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold text-slate-900 mb-2">
                  {language === 'pt' ? 'Posso mudar de plano?' : 'Can I change plans?'}
                </h3>
                <p className="text-slate-600 text-sm">
                  {language === 'pt' 
                    ? 'Sim! Você pode fazer upgrade ou downgrade a qualquer momento. A mudança será aplicada no próximo ciclo de faturamento.'
                    : 'Yes! You can upgrade or downgrade at any time. The change will be applied in the next billing cycle.'}
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold text-slate-900 mb-2">
                  {language === 'pt' ? 'Quando recebo os pagamentos?' : 'When do I receive payments?'}
                </h3>
                <p className="text-slate-600 text-sm">
                  {language === 'pt' 
                    ? 'Os pagamentos são processados automaticamente e transferidos para sua conta em até 7 dias úteis após a confirmação da matrícula.'
                    : 'Payments are processed automatically and transferred to your account within 7 business days after enrollment confirmation.'}
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold text-slate-900 mb-2">
                  {language === 'pt' ? 'Preciso de CNPJ ou documentos?' : 'Do I need business documents?'}
                </h3>
                <p className="text-slate-600 text-sm">
                  {language === 'pt' 
                    ? 'Sim, sua escola precisa ser uma instituição registrada. Verificaremos seus documentos durante o processo de aprovação.'
                    : 'Yes, your school needs to be a registered institution. We will verify your documents during the approval process.'}
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};
