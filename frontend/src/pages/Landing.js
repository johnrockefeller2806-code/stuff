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
  FileText
} from 'lucide-react';

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

  return (
    <div className="min-h-screen" data-testid="landing-page">
      {/* Hero Section */}
      <section className="relative hero-gradient text-white overflow-hidden">
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1668631629754-0ddbd0c252dd?w=1920')] bg-cover bg-center opacity-20" />
        <div className="relative max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-24 md:py-32">
          <div className="max-w-3xl">
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
              <Link to="/services">
                <Button 
                  variant="outline" 
                  size="lg" 
                  className="border-white/30 text-white hover:bg-white/10 rounded-full px-8 py-6 text-lg"
                  data-testid="hero-secondary-cta"
                >
                  {t('hero_secondary')}
                </Button>
              </Link>
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
