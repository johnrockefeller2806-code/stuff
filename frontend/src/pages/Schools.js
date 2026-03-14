import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { Star, MapPin, Search, Filter, ArrowRight, Lock, Sparkles } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const LOGO_URL = "https://customer-assets.emergentagent.com/job_dublin-study/artifacts/o9gnc0xi_WhatsApp%20Image%202026-01-11%20at%2023.59.07.jpeg";

export const Schools = () => {
  const { t, language } = useLanguage();
  const { user, isAuthenticated, isPlusUser } = useAuth();
  const navigate = useNavigate();
  const [schools, setSchools] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [schoolsRes, coursesRes] = await Promise.all([
        axios.get(`${API}/schools`),
        axios.get(`${API}/courses`)
      ]);
      setSchools(schoolsRes.data);
      setCourses(coursesRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMinPrice = (schoolId) => {
    const schoolCourses = courses.filter(c => c.school_id === schoolId);
    if (schoolCourses.length === 0) return null;
    return Math.min(...schoolCourses.map(c => c.price));
  };

  const filteredSchools = schools.filter(school =>
    school.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    school.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 py-12" data-testid="schools-loading">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <Skeleton className="h-12 w-64 mb-4" />
          <Skeleton className="h-6 w-96 mb-8" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map(i => (
              <Skeleton key={i} className="h-80 rounded-2xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Schools Page - Open to public
  return (
    <div className="min-h-screen bg-slate-50" data-testid="schools-page">
      {/* Header */}
      <div className="bg-emerald-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="font-serif text-4xl md:text-5xl font-bold" data-testid="schools-title">
                  {t('schools_title')}
                </h1>
                <Badge className="bg-amber-500 text-white">
                  <Sparkles className="h-3 w-3 mr-1" />
                  PLUS
                </Badge>
              </div>
              <p className="text-emerald-200 text-lg max-w-2xl">
                {t('schools_subtitle')}
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

      {/* Search & Filters */}
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 -mt-6">
        <Card className="border-none shadow-lg">
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <Input
                  placeholder={language === 'pt' ? 'Buscar escolas...' : 'Search schools...'}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 h-12 rounded-xl"
                  data-testid="schools-search"
                />
              </div>
              <Button variant="outline" className="h-12 px-6 rounded-xl gap-2">
                <Filter className="h-4 w-4" />
                {language === 'pt' ? 'Filtros' : 'Filters'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Schools Grid */}
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredSchools.map((school) => {
            const minPrice = getMinPrice(school.id);
            return (
              <Link to={`/schools/${school.id}`} key={school.id}>
                <Card 
                  className="group overflow-hidden border-slate-100 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300"
                  data-testid={`school-card-${school.id}`}
                >
                  <div className="relative h-48 overflow-hidden">
                    <img
                      src={school.image_url}
                      alt={school.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    <div className="absolute top-4 left-4 flex gap-2">
                      {school.accreditation?.slice(0, 2).map((acc, i) => (
                        <Badge key={i} className="bg-white/90 text-emerald-800 text-xs">
                          {acc}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-serif font-semibold text-xl text-slate-900 group-hover:text-emerald-800 transition-colors">
                        {school.name}
                      </h3>
                      <div className="flex items-center gap-1 text-amber-500">
                        <Star className="h-4 w-4 fill-current" />
                        <span className="text-sm font-medium">{school.rating}</span>
                        <span className="text-slate-400 text-xs">({school.reviews_count})</span>
                      </div>
                    </div>
                    <p className="text-slate-500 text-sm mb-4 line-clamp-2">
                      {language === 'pt' ? school.description : school.description_en}
                    </p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1 text-slate-400 text-sm">
                        <MapPin className="h-4 w-4" />
                        {school.address}
                      </div>
                      {minPrice && (
                        <div className="text-right">
                          <span className="text-xs text-slate-400">{t('schools_from')}</span>
                          <span className="block font-semibold text-emerald-700">
                            €{minPrice.toLocaleString()}
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
                      <div className="flex gap-2">
                        {school.facilities?.slice(0, 3).map((facility, i) => (
                          <Badge key={i} variant="secondary" className="text-xs">
                            {facility}
                          </Badge>
                        ))}
                      </div>
                      <ArrowRight className="h-5 w-5 text-slate-300 group-hover:text-emerald-600 transition-colors" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>

        {filteredSchools.length === 0 && (
          <div className="text-center py-16" data-testid="no-schools">
            <p className="text-slate-500">
              {language === 'pt' ? 'Nenhuma escola encontrada.' : 'No schools found.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
