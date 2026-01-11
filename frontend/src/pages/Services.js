import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../context/LanguageContext';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
import { 
  FileText, 
  Building2, 
  Plane,
  CreditCard,
  ArrowRight,
  MapPin,
  Phone,
  Globe,
  Clock
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const Services = () => {
  const { t, language } = useLanguage();
  const [agencies, setAgencies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAgencies();
  }, []);

  const fetchAgencies = async () => {
    try {
      const response = await axios.get(`${API}/services/agencies`);
      setAgencies(response.data);
    } catch (error) {
      console.error('Error fetching agencies:', error);
    } finally {
      setLoading(false);
    }
  };

  const guides = [
    {
      icon: CreditCard,
      title: t('services_pps'),
      description: t('services_pps_desc'),
      href: '/services/pps',
      color: 'bg-blue-100 text-blue-700',
    },
    {
      icon: FileText,
      title: t('services_gnib'),
      description: t('services_gnib_desc'),
      href: '/services/gnib',
      color: 'bg-purple-100 text-purple-700',
    },
    {
      icon: Plane,
      title: t('services_passport'),
      description: t('services_passport_desc'),
      href: '/services/passport',
      color: 'bg-amber-100 text-amber-700',
    },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 py-12" data-testid="services-loading">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <Skeleton className="h-12 w-64 mb-4" />
          <Skeleton className="h-6 w-96 mb-8" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            {[1, 2, 3].map(i => (
              <Skeleton key={i} className="h-48 rounded-xl" />
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map(i => (
              <Skeleton key={i} className="h-48 rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="services-page">
      {/* Header */}
      <div className="bg-emerald-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <h1 className="font-serif text-4xl md:text-5xl font-bold mb-4" data-testid="services-title">
            {t('services_title')}
          </h1>
          <p className="text-emerald-200 text-lg max-w-2xl">
            {t('services_subtitle')}
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-8">
        {/* Guides Section */}
        <div className="mb-12">
          <h2 className="font-serif text-2xl font-semibold text-slate-900 mb-6">
            {language === 'pt' ? 'Guias Essenciais' : 'Essential Guides'}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {guides.map((guide, index) => (
              <Link to={guide.href} key={index}>
                <Card 
                  className="group h-full border-slate-100 hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
                  data-testid={`guide-card-${index}`}
                >
                  <CardContent className="p-6">
                    <div className={`w-14 h-14 rounded-2xl ${guide.color} flex items-center justify-center mb-4`}>
                      <guide.icon className="h-7 w-7" />
                    </div>
                    <h3 className="font-semibold text-lg text-slate-900 mb-2 group-hover:text-emerald-700 transition-colors">
                      {guide.title}
                    </h3>
                    <p className="text-slate-500 text-sm mb-4">
                      {guide.description}
                    </p>
                    <div className="flex items-center text-emerald-700 text-sm font-medium">
                      {t('learn_more')}
                      <ArrowRight className="h-4 w-4 ml-1 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>

        {/* Agencies Section */}
        <div>
          <h2 className="font-serif text-2xl font-semibold text-slate-900 mb-6">
            {t('services_agencies')}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {agencies.map((agency) => (
              <Card 
                key={agency.id} 
                className="border-slate-100 hover:shadow-lg transition-shadow"
                data-testid={`agency-${agency.id}`}
              >
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-emerald-100 rounded-xl flex-shrink-0">
                      <Building2 className="h-6 w-6 text-emerald-700" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-slate-900 mb-1">
                        {language === 'pt' ? agency.name : agency.name_en}
                      </h3>
                      <p className="text-slate-500 text-sm mb-4">
                        {language === 'pt' ? agency.description : agency.description_en}
                      </p>
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2 text-slate-600">
                          <MapPin className="h-4 w-4 text-slate-400" />
                          {agency.address}
                        </div>
                        <div className="flex items-center gap-2 text-slate-600">
                          <Phone className="h-4 w-4 text-slate-400" />
                          {agency.phone}
                        </div>
                        <div className="flex items-center gap-2 text-slate-600">
                          <Clock className="h-4 w-4 text-slate-400" />
                          {agency.opening_hours}
                        </div>
                      </div>

                      {agency.services && agency.services.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-slate-100">
                          <div className="flex flex-wrap gap-1">
                            {agency.services.map((service, i) => (
                              <Badge key={i} variant="secondary" className="text-xs">
                                {service}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      <a 
                        href={agency.website} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 mt-4 text-sm text-emerald-700 hover:text-emerald-800 font-medium"
                      >
                        <Globe className="h-4 w-4" />
                        {language === 'pt' ? 'Visitar site' : 'Visit website'}
                      </a>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
