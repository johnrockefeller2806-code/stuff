import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../context/LanguageContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Bus, 
  Train, 
  Clock, 
  MapPin,
  Euro,
  Info
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const LOGO_URL = "https://customer-assets.emergentagent.com/job_dublin-study/artifacts/o9gnc0xi_WhatsApp%20Image%202026-01-11%20at%2023.59.07.jpeg";
const TRANSPORT_IMAGE_URL = "https://customer-assets.emergentagent.com/job_dublin-exchange/artifacts/nalcqm7v_WhatsApp%20Image%202026-01-12%20at%2003.09.13.jpeg";

export const Transport = () => {
  const { t, language } = useLanguage();
  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRoutes();
  }, []);

  const fetchRoutes = async () => {
    try {
      const response = await axios.get(`${API}/transport/routes`);
      setRoutes(response.data);
    } catch (error) {
      console.error('Error fetching routes:', error);
    } finally {
      setLoading(false);
    }
  };

  const busRoutes = routes.filter(r => !r.route_number.includes('LUAS') && !r.route_number.includes('DART'));
  const tramRoutes = routes.filter(r => r.route_number.includes('LUAS'));
  const trainRoutes = routes.filter(r => r.route_number.includes('DART'));

  const RouteCard = ({ route }) => {
    const isTram = route.route_number.includes('LUAS');
    const isTrain = route.route_number.includes('DART');
    
    return (
      <Card className="border-slate-100 hover:shadow-lg transition-shadow" data-testid={`route-${route.id}`}>
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-xl ${isTrain ? 'bg-green-100' : isTram ? 'bg-purple-100' : 'bg-blue-100'}`}>
                {isTrain ? (
                  <Train className={`h-6 w-6 ${isTrain ? 'text-green-700' : 'text-purple-700'}`} />
                ) : (
                  <Bus className={`h-6 w-6 ${isTram ? 'text-purple-700' : 'text-blue-700'}`} />
                )}
              </div>
              <div>
                <Badge className={`${isTrain ? 'bg-green-600' : isTram ? 'bg-purple-600' : 'bg-blue-600'} text-white`}>
                  {route.route_number}
                </Badge>
                <h3 className="font-semibold text-slate-900 mt-1">
                  {language === 'pt' ? route.name : route.name_en}
                </h3>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-500">{t('transport_fare')}</p>
              <p className="font-semibold text-emerald-700">€{route.fare.toFixed(2)}</p>
            </div>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <MapPin className="h-4 w-4 text-slate-400" />
              <span>{route.from_location} → {route.to_location}</span>
            </div>
            
            <div className="flex flex-wrap gap-4 text-sm text-slate-600">
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4 text-slate-400" />
                <span>{language === 'pt' ? 'A cada' : 'Every'} {route.frequency_minutes} min</span>
              </div>
              <div>
                <span className="text-slate-400">{t('transport_first')}:</span> {route.first_bus}
              </div>
              <div>
                <span className="text-slate-400">{t('transport_last')}:</span> {route.last_bus}
              </div>
            </div>
            
            {route.popular_stops && route.popular_stops.length > 0 && (
              <div className="pt-3 border-t border-slate-100">
                <p className="text-xs text-slate-400 mb-2">
                  {language === 'pt' ? 'Paradas principais:' : 'Popular stops:'}
                </p>
                <div className="flex flex-wrap gap-1">
                  {route.popular_stops.map((stop, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">
                      {stop}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 py-12" data-testid="transport-loading">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <Skeleton className="h-12 w-64 mb-4" />
          <Skeleton className="h-6 w-96 mb-8" />
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
    <div className="min-h-screen bg-slate-50" data-testid="transport-page">
      {/* Header */}
      <div className="relative bg-emerald-900 text-white py-16 overflow-hidden">
        {/* Background Image - Left Side */}
        <div className="absolute left-0 top-0 bottom-0 w-1/3 opacity-20">
          <img 
            src={TRANSPORT_IMAGE_URL}
            alt=""
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-transparent to-emerald-900" />
        </div>
        
        <div className="relative max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-serif text-4xl md:text-5xl font-bold mb-4" data-testid="transport-title">
                {t('transport_title')}
              </h1>
              <p className="text-emerald-200 text-lg max-w-2xl">
                {t('transport_subtitle')}
              </p>
            </div>
            <img 
              src={LOGO_URL} 
              alt="STUFF Intercâmbio" 
              className="h-16 md:h-20 w-auto object-contain bg-white/10 backdrop-blur-sm rounded-xl p-2 hidden sm:block"
            />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-8">
        {/* Info Card */}
        <Card className="border-slate-100 bg-emerald-50 mb-8" data-testid="transport-info">
          <CardContent className="p-6 flex items-start gap-4">
            <Info className="h-6 w-6 text-emerald-700 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-emerald-900 mb-1">
                {language === 'pt' ? 'Dica: Use o Leap Card!' : 'Tip: Use Leap Card!'}
              </h3>
              <p className="text-sm text-emerald-700">
                {language === 'pt' 
                  ? 'O Leap Card é um cartão recarregável que oferece tarifas mais baratas em todos os transportes públicos de Dublin. Você pode comprar em estações do Luas, lojas de conveniência e online.'
                  : 'The Leap Card is a rechargeable card that offers cheaper fares on all Dublin public transport. You can buy it at Luas stations, convenience stores and online.'}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs defaultValue="all" className="space-y-6">
          <TabsList className="bg-white border border-slate-100 p-1">
            <TabsTrigger value="all" data-testid="tab-all">
              {language === 'pt' ? 'Todos' : 'All'}
            </TabsTrigger>
            <TabsTrigger value="bus" data-testid="tab-bus">
              <Bus className="h-4 w-4 mr-1" />
              Bus
            </TabsTrigger>
            <TabsTrigger value="luas" data-testid="tab-luas">
              <Train className="h-4 w-4 mr-1" />
              Luas
            </TabsTrigger>
            <TabsTrigger value="dart" data-testid="tab-dart">
              <Train className="h-4 w-4 mr-1" />
              DART
            </TabsTrigger>
          </TabsList>

          <TabsContent value="all">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {routes.map(route => (
                <RouteCard key={route.id} route={route} />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="bus">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {busRoutes.map(route => (
                <RouteCard key={route.id} route={route} />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="luas">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {tramRoutes.map(route => (
                <RouteCard key={route.id} route={route} />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="dart">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {trainRoutes.map(route => (
                <RouteCard key={route.id} route={route} />
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};
