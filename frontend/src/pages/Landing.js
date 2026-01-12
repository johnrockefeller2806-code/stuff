import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { 
  GraduationCap, 
  CreditCard, 
  BookOpen, 
  HeadphonesIcon,
  ArrowRight,
  Star,
  MapPin,
  Bus,
  FileText,
  Shield,
  Building2,
  Euro,
  Mail,
  FileCheck,
  CheckCircle,
  Zap,
  Heart,
  Lock
} from 'lucide-react';

const LOGO_URL = "https://customer-assets.emergentagent.com/job_dublin-study/artifacts/o9gnc0xi_WhatsApp%20Image%202026-01-11%20at%2023.59.07.jpeg";
const HERO_IMAGE_URL = "https://customer-assets.emergentagent.com/job_dublin-exchange/artifacts/498i1soq_WhatsApp%20Image%202026-01-12%20at%2000.30.29.jpeg";

export const Landing = () => {
  const { t, language } = useLanguage();

  const features = [
    {
      icon: GraduationCap,
      title: t('feature_schools'),
      description: t('feature_schools_desc'),
    },
    {
      icon: CreditCard,
      title: t('feature_payment'),
      description: t('feature_payment_desc'),
    },
    {
      icon: BookOpen,
      title: t('feature_guides'),
      description: t('feature_guides_desc'),
    },
    {
      icon: HeadphonesIcon,
      title: t('feature_support'),
      description: t('feature_support_desc'),
    },
  ];

  const quickLinks = [
    {
      icon: GraduationCap,
      title: language === 'pt' ? 'Escolas' : 'Schools',
      desc: language === 'pt' ? 'Encontre sua escola ideal' : 'Find your ideal school',
      href: '/schools',
      color: 'bg-emerald-100 text-emerald-700',
    },
    {
      icon: Bus,
      title: language === 'pt' ? 'Transporte' : 'Transport',
      desc: language === 'pt' ? 'Rotas e horários' : 'Routes and schedules',
      href: '/transport',
      color: 'bg-amber-100 text-amber-700',
    },
    {
      icon: FileText,
      title: language === 'pt' ? 'Documentos' : 'Documents',
      desc: language === 'pt' ? 'PPS, GNIB e mais' : 'PPS, GNIB and more',
      href: '/services',
      color: 'bg-blue-100 text-blue-700',
    },
  ];

  const benefits = [
    {
      icon: Shield,
      title: language === 'pt' ? 'Segurança absoluta' : 'Absolute security',
      desc: language === 'pt' ? 'Em todo o processo' : 'Throughout the process',
    },
    {
      icon: Building2,
      title: language === 'pt' ? 'Contato direto' : 'Direct contact',
      desc: language === 'pt' ? 'Com a escola, sem intermediários' : 'With the school, no middlemen',
    },
    {
      icon: Euro,
      title: language === 'pt' ? 'Preços reais' : 'Real prices',
      desc: language === 'pt' ? 'Diferenciados e exclusivos' : 'Differentiated and exclusive',
    },
    {
      icon: Lock,
      title: language === 'pt' ? 'Pagamento 100% seguro' : '100% secure payment',
      desc: language === 'pt' ? 'Direto pela plataforma' : 'Direct through platform',
    },
    {
      icon: Mail,
      title: language === 'pt' ? 'Confirmação imediata' : 'Immediate confirmation',
      desc: language === 'pt' ? 'Por e-mail após o pagamento' : 'By email after payment',
    },
    {
      icon: FileCheck,
      title: language === 'pt' ? 'Carta oficial' : 'Official letter',
      desc: language === 'pt' ? 'Em até 5 dias úteis' : 'Within 5 business days',
    },
  ];

  return (
    <div className="min-h-screen" data-testid="landing-page">
      {/* Hero Section */}
      <section className="relative hero-gradient text-white overflow-hidden">
        {/* Background Image */}
        <div className="absolute inset-0">
          <img 
            src={HERO_IMAGE_URL} 
            alt="" 
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-emerald-900/85 via-emerald-900/70 to-emerald-800/60" />
        </div>
        <div className="relative max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-24 md:py-32">
          <div className="max-w-3xl">
            {/* Logo STUFF Intercâmbio */}
            <div className="mb-8 animate-fade-in">
              <img 
                src={LOGO_URL} 
                alt="STUFF Intercâmbio" 
                className="h-20 md:h-24 w-auto object-contain bg-white/10 backdrop-blur-sm rounded-2xl p-3"
                data-testid="hero-logo"
              />
            </div>
            <h1 className="font-serif text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-6 animate-fade-in" data-testid="hero-title">
              {t('hero_title')}
            </h1>
            <p className="text-lg md:text-xl text-emerald-100 mb-8 leading-relaxed animate-fade-in stagger-1" data-testid="hero-subtitle">
              {t('hero_subtitle')}
            </p>
            <div className="flex flex-col sm:flex-row gap-4 animate-fade-in stagger-2 relative z-10">
              <Link to="/schools">
                <Button 
                  size="lg" 
                  className="bg-amber-600 hover:bg-amber-500 text-white rounded-full px-8 py-6 text-lg font-medium shadow-lg hover:shadow-xl transition-all"
                  data-testid="hero-cta"
                >
                  {t('hero_cta')}
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <a href="#como-funciona">
                <Button 
                  variant="outline" 
                  size="lg" 
                  className="border-white/30 text-white hover:bg-white/10 rounded-full px-8 py-6 text-lg"
                  data-testid="hero-secondary-cta"
                >
                  {t('hero_secondary')}
                </Button>
              </a>
            </div>
          </div>
        </div>
        
        {/* Wave decoration */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 120L60 110C120 100 240 80 360 70C480 60 600 60 720 65C840 70 960 80 1080 85C1200 90 1320 90 1380 90L1440 90V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" fill="white"/>
          </svg>
        </div>
      </section>

      {/* Quick Links Section */}
      <section className="py-8 -mt-8 relative z-10">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {quickLinks.map((link, index) => (
              <Link to={link.href} key={index}>
                <Card className="group hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border-slate-100" data-testid={`quick-link-${index}`}>
                  <CardContent className="p-6 flex items-center gap-4">
                    <div className={`p-3 rounded-xl ${link.color}`}>
                      <link.icon className="h-6 w-6" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900">{link.title}</h3>
                      <p className="text-sm text-slate-500">{link.desc}</p>
                    </div>
                    <ArrowRight className="h-5 w-5 text-slate-300 group-hover:text-emerald-600 ml-auto transition-colors" />
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="como-funciona" className="py-20 md:py-28 bg-white" data-testid="how-it-works-section">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          {/* Header */}
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-2 bg-emerald-100 text-emerald-800 rounded-full text-sm font-medium mb-4">
              {language === 'pt' ? 'Como Funciona' : 'How It Works'}
            </span>
            <h2 className="font-serif text-3xl md:text-4xl lg:text-5xl font-bold text-slate-900 mb-6">
              {language === 'pt' 
                ? 'O intercâmbio do jeito certo.' 
                : 'Exchange the right way.'}
              <br />
              <span className="text-emerald-700">
                {language === 'pt' ? 'Direto com a escola.' : 'Direct with the school.'}
              </span>
            </h2>
            <p className="text-lg text-slate-600 max-w-3xl mx-auto leading-relaxed">
              {language === 'pt'
                ? 'Chega de intermediários, agenciadores e taxas escondidas. Nosso aplicativo coloca você em contato direto com as escolas na Irlanda, de forma simples, segura e transparente.'
                : 'No more middlemen, agents or hidden fees. Our app puts you in direct contact with schools in Ireland, simply, safely and transparently.'}
            </p>
          </div>

          {/* Exclusive Access Card */}
          <Card className="bg-gradient-to-br from-emerald-900 to-emerald-800 text-white border-none mb-16 overflow-hidden">
            <CardContent className="p-8 md:p-12 relative">
              <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-700/30 rounded-full blur-3xl" />
              <div className="relative">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-amber-500 rounded-lg">
                    <Star className="h-5 w-5 text-white" />
                  </div>
                  <span className="text-amber-400 font-medium">
                    {language === 'pt' ? 'Acesso Exclusivo' : 'Exclusive Access'}
                  </span>
                </div>
                <p className="text-xl md:text-2xl text-emerald-100 leading-relaxed max-w-4xl">
                  {language === 'pt'
                    ? 'Aqui, você tem acesso exclusivo a escolas cadastradas e verificadas, com preços diferenciados, negociados diretamente para usuários da plataforma. Tudo isso sem comissões abusivas e sem terceiros envolvidos.'
                    : 'Here, you have exclusive access to registered and verified schools, with differentiated prices, negotiated directly for platform users. All without abusive commissions and without third parties involved.'}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Benefits Grid */}
          <div className="mb-16">
            <h3 className="font-serif text-2xl font-semibold text-slate-900 text-center mb-8">
              {language === 'pt' ? 'Por que usar nosso aplicativo?' : 'Why use our app?'}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {benefits.map((benefit, index) => (
                <Card key={index} className="border-slate-100 hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
                  <CardContent className="p-6 flex items-start gap-4">
                    <div className="p-3 bg-emerald-100 rounded-xl flex-shrink-0">
                      <benefit.icon className="h-6 w-6 text-emerald-700" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-1">{benefit.title}</h4>
                      <p className="text-sm text-slate-500">{benefit.desc}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Process Steps */}
          <div className="bg-slate-50 rounded-3xl p-8 md:p-12 mb-16">
            <h3 className="font-serif text-2xl font-semibold text-slate-900 text-center mb-8">
              {language === 'pt' ? 'Simples. Transparente. Confiável.' : 'Simple. Transparent. Reliable.'}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[
                {
                  step: '1',
                  title: language === 'pt' ? 'Escolha a escola' : 'Choose the school',
                  desc: language === 'pt' ? 'Navegue pelas escolas verificadas' : 'Browse verified schools',
                  icon: Building2
                },
                {
                  step: '2',
                  title: language === 'pt' ? 'Veja o valor real' : 'See the real price',
                  desc: language === 'pt' ? 'Preços transparentes, sem surpresas' : 'Transparent prices, no surprises',
                  icon: Euro
                },
                {
                  step: '3',
                  title: language === 'pt' ? 'Pague com segurança' : 'Pay securely',
                  desc: language === 'pt' ? 'Pagamento protegido via Stripe' : 'Protected payment via Stripe',
                  icon: Lock
                },
                {
                  step: '4',
                  title: language === 'pt' ? 'Receba a confirmação' : 'Get confirmation',
                  desc: language === 'pt' ? 'Carta oficial em até 5 dias úteis' : 'Official letter within 5 days',
                  icon: FileCheck
                }
              ].map((item, index) => (
                <div key={index} className="text-center">
                  <div className="relative inline-flex items-center justify-center w-16 h-16 bg-emerald-900 rounded-2xl mb-4">
                    <item.icon className="h-7 w-7 text-white" />
                    <span className="absolute -top-2 -right-2 w-6 h-6 bg-amber-500 rounded-full text-white text-sm font-bold flex items-center justify-center">
                      {item.step}
                    </span>
                  </div>
                  <h4 className="font-semibold text-slate-900 mb-1">{item.title}</h4>
                  <p className="text-sm text-slate-500">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Value Propositions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <Card className="bg-emerald-50 border-emerald-100">
              <CardContent className="p-6 text-center">
                <Zap className="h-10 w-10 text-emerald-600 mx-auto mb-4" />
                <h4 className="font-semibold text-emerald-900 mb-2">
                  {language === 'pt' ? 'Mais autonomia' : 'More autonomy'}
                </h4>
                <p className="text-sm text-emerald-700">
                  {language === 'pt' 
                    ? 'Você decide tudo, com controle total do processo' 
                    : 'You decide everything, with full control of the process'}
                </p>
              </CardContent>
            </Card>
            <Card className="bg-amber-50 border-amber-100">
              <CardContent className="p-6 text-center">
                <Euro className="h-10 w-10 text-amber-600 mx-auto mb-4" />
                <h4 className="font-semibold text-amber-900 mb-2">
                  {language === 'pt' ? 'Mais economia' : 'More savings'}
                </h4>
                <p className="text-sm text-amber-700">
                  {language === 'pt' 
                    ? 'Sem taxas de intermediários ou custos extras' 
                    : 'No middleman fees or extra costs'}
                </p>
              </CardContent>
            </Card>
            <Card className="bg-blue-50 border-blue-100">
              <CardContent className="p-6 text-center">
                <Heart className="h-10 w-10 text-blue-600 mx-auto mb-4" />
                <h4 className="font-semibold text-blue-900 mb-2">
                  {language === 'pt' ? 'Mais confiança' : 'More trust'}
                </h4>
                <p className="text-sm text-blue-700">
                  {language === 'pt' 
                    ? 'Escolas verificadas e processo transparente' 
                    : 'Verified schools and transparent process'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Final Message */}
          <div className="text-center">
            <p className="text-lg text-slate-600 mb-6 max-w-2xl mx-auto">
              {language === 'pt'
                ? 'Nosso aplicativo foi criado para quem quer fazer intercâmbio com controle total, evitando surpresas, burocracias desnecessárias e custos extras.'
                : 'Our app was created for those who want to exchange with full control, avoiding surprises, unnecessary bureaucracy and extra costs.'}
            </p>
            <p className="text-xl font-semibold text-emerald-800 mb-8">
              {language === 'pt'
                ? 'Aqui, você decide. A escola confirma. E o seu intercâmbio acontece.'
                : 'Here, you decide. The school confirms. And your exchange happens.'}
            </p>
            <div className="flex flex-wrap justify-center gap-4 text-sm text-slate-500">
              <span className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-emerald-600" />
                {language === 'pt' ? 'Sem atravessadores' : 'No middlemen'}
              </span>
              <span className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-emerald-600" />
                {language === 'pt' ? 'Sem complicação' : 'No complications'}
              </span>
              <span className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-emerald-600" />
                {language === 'pt' ? 'Sem risco' : 'No risk'}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 md:py-28 bg-slate-50" data-testid="features-section">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <div className="text-center mb-16">
            <h2 className="font-serif text-3xl md:text-4xl font-semibold text-emerald-900 mb-4">
              {t('features_title')}
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <Card 
                key={index} 
                className="bg-white border-none shadow-sm hover:shadow-lg transition-shadow"
                data-testid={`feature-card-${index}`}
              >
                <CardContent className="p-8 text-center">
                  <div className="inline-flex items-center justify-center w-14 h-14 bg-emerald-100 rounded-2xl mb-6">
                    <feature.icon className="h-7 w-7 text-emerald-700" />
                  </div>
                  <h3 className="font-semibold text-lg text-slate-900 mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-slate-500 text-sm leading-relaxed">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-emerald-900 text-white">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div data-testid="stat-schools">
              <div className="text-4xl md:text-5xl font-bold text-amber-400 mb-2">15+</div>
              <div className="text-emerald-200 text-sm">{language === 'pt' ? 'Escolas Parceiras' : 'Partner Schools'}</div>
            </div>
            <div data-testid="stat-students">
              <div className="text-4xl md:text-5xl font-bold text-amber-400 mb-2">500+</div>
              <div className="text-emerald-200 text-sm">{language === 'pt' ? 'Estudantes' : 'Students'}</div>
            </div>
            <div data-testid="stat-rating">
              <div className="text-4xl md:text-5xl font-bold text-amber-400 mb-2 flex items-center justify-center gap-1">
                4.9 <Star className="h-6 w-6 fill-amber-400" />
              </div>
              <div className="text-emerald-200 text-sm">{language === 'pt' ? 'Avaliação Média' : 'Average Rating'}</div>
            </div>
            <div data-testid="stat-support">
              <div className="text-4xl md:text-5xl font-bold text-amber-400 mb-2">24/7</div>
              <div className="text-emerald-200 text-sm">{language === 'pt' ? 'Suporte' : 'Support'}</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 md:py-28">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <div className="bg-gradient-to-br from-emerald-50 to-emerald-100/50 rounded-3xl p-8 md:p-16 text-center">
            <h2 className="font-serif text-3xl md:text-4xl font-semibold text-emerald-900 mb-4">
              {language === 'pt' ? 'Pronto para começar?' : 'Ready to start?'}
            </h2>
            <p className="text-slate-600 mb-8 max-w-2xl mx-auto">
              {language === 'pt' 
                ? 'Explore nossas escolas parceiras e encontre o curso perfeito para você.'
                : 'Explore our partner schools and find the perfect course for you.'}
            </p>
            <Link to="/schools">
              <Button 
                size="lg" 
                className="bg-emerald-900 hover:bg-emerald-800 rounded-full px-8 py-6 text-lg"
                data-testid="cta-button"
              >
                {t('hero_cta')}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
