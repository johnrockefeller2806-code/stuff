import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useLanguage } from '../context/LanguageContext';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import { 
  ArrowLeft,
  CheckCircle,
  ExternalLink,
  FileText,
  Calendar,
  Euro,
  Lightbulb,
  Link as LinkIcon
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const GuideLayout = ({ title, children, loading }) => {
  const navigate = useNavigate();
  const { language } = useLanguage();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 py-12">
        <div className="max-w-3xl mx-auto px-6">
          <Skeleton className="h-8 w-32 mb-8" />
          <Skeleton className="h-12 w-96 mb-4" />
          <Skeleton className="h-6 w-full mb-8" />
          <Skeleton className="h-64 rounded-xl mb-4" />
          <Skeleton className="h-64 rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="guide-page">
      {/* Header */}
      <div className="bg-emerald-900 text-white py-12">
        <div className="max-w-3xl mx-auto px-6">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => navigate('/services')}
            className="text-emerald-200 hover:text-white hover:bg-emerald-800 mb-4"
            data-testid="back-button"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            {language === 'pt' ? 'Voltar' : 'Back'}
          </Button>
          <h1 className="font-serif text-3xl md:text-4xl font-bold" data-testid="guide-title">
            {title}
          </h1>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-6 py-8">
        {children}
      </div>
    </div>
  );
};

export const PPSGuide = () => {
  const { language } = useLanguage();
  const [guide, setGuide] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGuide();
  }, []);

  const fetchGuide = async () => {
    try {
      const response = await axios.get(`${API}/guides/pps`);
      setGuide(response.data);
    } catch (error) {
      console.error('Error fetching guide:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <GuideLayout 
      title={language === 'pt' ? guide?.title : guide?.title_en} 
      loading={loading}
    >
      {guide && (
        <div className="space-y-8">
          {/* Description */}
          <Card className="border-slate-100 bg-emerald-50">
            <CardContent className="p-6">
              <p className="text-emerald-800">{guide.description}</p>
            </CardContent>
          </Card>

          {/* Steps */}
          <div className="space-y-4">
            <h2 className="font-serif text-xl font-semibold text-slate-900">
              {language === 'pt' ? 'Passo a Passo' : 'Step by Step'}
            </h2>
            {guide.steps.map((step, index) => (
              <Card key={index} className="border-slate-100" data-testid={`step-${index}`}>
                <CardContent className="p-6">
                  <div className="flex gap-4">
                    <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="font-bold text-emerald-700">{step.step}</span>
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-slate-900 mb-2">
                        {language === 'pt' ? step.title : step.title_en}
                      </h3>
                      <p className="text-slate-600 text-sm mb-3">{step.description}</p>
                      
                      {step.documents && (
                        <div className="mt-3">
                          <p className="text-xs text-slate-500 mb-2">
                            {language === 'pt' ? 'Documentos necessários:' : 'Required documents:'}
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {step.documents.map((doc, i) => (
                              <Badge key={i} variant="secondary" className="text-xs">
                                <FileText className="h-3 w-3 mr-1" />
                                {doc}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {step.link && (
                        <a 
                          href={step.link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 mt-3 text-sm text-emerald-700 hover:text-emerald-800"
                        >
                          <ExternalLink className="h-4 w-4" />
                          {language === 'pt' ? 'Acessar' : 'Access'}
                        </a>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Tips */}
          <Card className="border-slate-100 bg-amber-50">
            <CardContent className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <Lightbulb className="h-5 w-5 text-amber-600" />
                <h3 className="font-semibold text-amber-900">
                  {language === 'pt' ? 'Dicas Importantes' : 'Important Tips'}
                </h3>
              </div>
              <ul className="space-y-2">
                {guide.tips.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-amber-800">
                    <CheckCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                    {tip}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {/* Useful Links */}
          <div>
            <h2 className="font-serif text-xl font-semibold text-slate-900 mb-4">
              {language === 'pt' ? 'Links Úteis' : 'Useful Links'}
            </h2>
            <div className="flex flex-wrap gap-3">
              {guide.useful_links.map((link, i) => (
                <a
                  key={i}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm text-slate-700 hover:border-emerald-300 hover:text-emerald-700 transition-colors"
                >
                  <LinkIcon className="h-4 w-4" />
                  {link.name}
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </GuideLayout>
  );
};

export const GNIBGuide = () => {
  const { language } = useLanguage();
  const [guide, setGuide] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGuide();
  }, []);

  const fetchGuide = async () => {
    try {
      const response = await axios.get(`${API}/guides/gnib`);
      setGuide(response.data);
    } catch (error) {
      console.error('Error fetching guide:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <GuideLayout 
      title={language === 'pt' ? guide?.title : guide?.title_en} 
      loading={loading}
    >
      {guide && (
        <div className="space-y-8">
          {/* Description */}
          <Card className="border-slate-100 bg-emerald-50">
            <CardContent className="p-6">
              <p className="text-emerald-800">{guide.description}</p>
            </CardContent>
          </Card>

          {/* Costs */}
          <Card className="border-slate-100 bg-blue-50">
            <CardContent className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <Euro className="h-5 w-5 text-blue-600" />
                <h3 className="font-semibold text-blue-900">
                  {language === 'pt' ? 'Custos' : 'Costs'}
                </h3>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-blue-700">{language === 'pt' ? 'Taxa de registro' : 'Registration fee'}</p>
                  <p className="text-2xl font-bold text-blue-900">€{guide.costs.registration_fee}</p>
                </div>
                <div>
                  <p className="text-sm text-blue-700">{language === 'pt' ? 'Extrato mínimo' : 'Minimum statement'}</p>
                  <p className="text-2xl font-bold text-blue-900">€{guide.costs.bank_statement_minimum.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Steps */}
          <div className="space-y-4">
            <h2 className="font-serif text-xl font-semibold text-slate-900">
              {language === 'pt' ? 'Passo a Passo' : 'Step by Step'}
            </h2>
            {guide.steps.map((step, index) => (
              <Card key={index} className="border-slate-100" data-testid={`step-${index}`}>
                <CardContent className="p-6">
                  <div className="flex gap-4">
                    <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="font-bold text-purple-700">{step.step}</span>
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-slate-900 mb-2">
                        {language === 'pt' ? step.title : step.title_en}
                      </h3>
                      <p className="text-slate-600 text-sm mb-3">{step.description}</p>
                      
                      {step.documents && (
                        <div className="mt-3">
                          <p className="text-xs text-slate-500 mb-2">
                            {language === 'pt' ? 'Documentos necessários:' : 'Required documents:'}
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {step.documents.map((doc, i) => (
                              <Badge key={i} variant="secondary" className="text-xs">
                                <FileText className="h-3 w-3 mr-1" />
                                {doc}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {step.link && (
                        <a 
                          href={step.link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 mt-3 text-sm text-emerald-700 hover:text-emerald-800"
                        >
                          <ExternalLink className="h-4 w-4" />
                          {language === 'pt' ? 'Acessar' : 'Access'}
                        </a>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Tips */}
          <Card className="border-slate-100 bg-amber-50">
            <CardContent className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <Lightbulb className="h-5 w-5 text-amber-600" />
                <h3 className="font-semibold text-amber-900">
                  {language === 'pt' ? 'Dicas Importantes' : 'Important Tips'}
                </h3>
              </div>
              <ul className="space-y-2">
                {guide.tips.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-amber-800">
                    <CheckCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                    {tip}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {/* Useful Links */}
          <div>
            <h2 className="font-serif text-xl font-semibold text-slate-900 mb-4">
              {language === 'pt' ? 'Links Úteis' : 'Useful Links'}
            </h2>
            <div className="flex flex-wrap gap-3">
              {guide.useful_links.map((link, i) => (
                <a
                  key={i}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm text-slate-700 hover:border-emerald-300 hover:text-emerald-700 transition-colors"
                >
                  <LinkIcon className="h-4 w-4" />
                  {link.name}
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </GuideLayout>
  );
};

export const PassportGuide = () => {
  const { language } = useLanguage();
  const [guide, setGuide] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGuide();
  }, []);

  const fetchGuide = async () => {
    try {
      const response = await axios.get(`${API}/guides/passport`);
      setGuide(response.data);
    } catch (error) {
      console.error('Error fetching guide:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <GuideLayout 
      title={language === 'pt' ? guide?.title : guide?.title_en} 
      loading={loading}
    >
      {guide && (
        <div className="space-y-8">
          {/* Description */}
          <Card className="border-slate-100 bg-emerald-50">
            <CardContent className="p-6">
              <p className="text-emerald-800">{guide.description}</p>
            </CardContent>
          </Card>

          {/* Costs & Validity */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="border-slate-100 bg-blue-50">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Euro className="h-5 w-5 text-blue-600" />
                  <h3 className="font-semibold text-blue-900">
                    {language === 'pt' ? 'Valores' : 'Costs'}
                  </h3>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-blue-700">{language === 'pt' ? 'Normal' : 'Regular'}</span>
                    <span className="font-bold text-blue-900">R$ {guide.costs.regular.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-blue-700">{language === 'pt' ? 'Emergencial' : 'Emergency'}</span>
                    <span className="font-bold text-blue-900">R$ {guide.costs.emergency.toFixed(2)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-100 bg-green-50">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Calendar className="h-5 w-5 text-green-600" />
                  <h3 className="font-semibold text-green-900">
                    {language === 'pt' ? 'Validade' : 'Validity'}
                  </h3>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-green-700">{language === 'pt' ? 'Adultos' : 'Adults'}</span>
                    <span className="font-bold text-green-900">{guide.validity.adults}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-green-700">{language === 'pt' ? 'Menores' : 'Minors'}</span>
                    <span className="font-bold text-green-900">{guide.validity.minors}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Steps */}
          <div className="space-y-4">
            <h2 className="font-serif text-xl font-semibold text-slate-900">
              {language === 'pt' ? 'Passo a Passo' : 'Step by Step'}
            </h2>
            {guide.steps.map((step, index) => (
              <Card key={index} className="border-slate-100" data-testid={`step-${index}`}>
                <CardContent className="p-6">
                  <div className="flex gap-4">
                    <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="font-bold text-amber-700">{step.step}</span>
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-slate-900 mb-2">
                        {language === 'pt' ? step.title : step.title_en}
                      </h3>
                      <p className="text-slate-600 text-sm mb-3">{step.description}</p>
                      
                      {step.documents && (
                        <div className="mt-3">
                          <p className="text-xs text-slate-500 mb-2">
                            {language === 'pt' ? 'Documentos necessários:' : 'Required documents:'}
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {step.documents.map((doc, i) => (
                              <Badge key={i} variant="secondary" className="text-xs">
                                <FileText className="h-3 w-3 mr-1" />
                                {doc}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {step.link && (
                        <a 
                          href={step.link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 mt-3 text-sm text-emerald-700 hover:text-emerald-800"
                        >
                          <ExternalLink className="h-4 w-4" />
                          {language === 'pt' ? 'Acessar' : 'Access'}
                        </a>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Tips */}
          <Card className="border-slate-100 bg-amber-50">
            <CardContent className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <Lightbulb className="h-5 w-5 text-amber-600" />
                <h3 className="font-semibold text-amber-900">
                  {language === 'pt' ? 'Dicas Importantes' : 'Important Tips'}
                </h3>
              </div>
              <ul className="space-y-2">
                {guide.tips.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-amber-800">
                    <CheckCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                    {tip}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {/* Useful Links */}
          <div>
            <h2 className="font-serif text-xl font-semibold text-slate-900 mb-4">
              {language === 'pt' ? 'Links Úteis' : 'Useful Links'}
            </h2>
            <div className="flex flex-wrap gap-3">
              {guide.useful_links.map((link, i) => (
                <a
                  key={i}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm text-slate-700 hover:border-emerald-300 hover:text-emerald-700 transition-colors"
                >
                  <LinkIcon className="h-4 w-4" />
                  {link.name}
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </GuideLayout>
  );
};

export const DrivingLicenseGuide = () => {
  const { language } = useLanguage();
  const [guide, setGuide] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGuide();
  }, []);

  const fetchGuide = async () => {
    try {
      const response = await axios.get(`${API}/guides/driving-license`);
      setGuide(response.data);
    } catch (error) {
      console.error('Error fetching guide:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <GuideLayout 
      title={language === 'pt' ? guide?.title : guide?.title_en} 
      loading={loading}
    >
      {guide && (
        <div className="space-y-8">
          {/* Introduction */}
          <Card className="border-slate-100 bg-emerald-50">
            <CardContent className="p-6">
              <p className="text-emerald-800">
                {language === 'pt' ? guide.intro?.pt : guide.intro?.en}
              </p>
            </CardContent>
          </Card>

          {/* Important Notes */}
          {guide.important_notes && (
            <div className="space-y-4">
              {guide.important_notes.map((note, i) => (
                <Card key={i} className="border-red-200 bg-red-50">
                  <CardContent className="p-4">
                    <h4 className="font-semibold text-red-900 mb-2">{note.title}</h4>
                    <p className="text-sm text-red-800">{note.content}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Options */}
          {guide.options && (
            <div>
              <h2 className="font-serif text-xl font-semibold text-slate-900 mb-4">
                {language === 'pt' ? 'Suas Opções' : 'Your Options'}
              </h2>
              <div className="grid grid-cols-1 gap-4">
                {guide.options.map((option, i) => (
                  <Card key={i} className="border-slate-100">
                    <CardContent className="p-4">
                      <h4 className="font-semibold text-slate-900 mb-1">
                        {language === 'pt' ? option.title : option.title_en}
                      </h4>
                      <p className="text-sm text-slate-600 mb-2">
                        {language === 'pt' ? option.description : option.description_en}
                      </p>
                      {option.requirements && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {option.requirements.map((req, j) => (
                            <Badge key={j} variant="secondary" className="text-xs">{req}</Badge>
                          ))}
                        </div>
                      )}
                      {option.note && (
                        <p className="text-xs text-amber-700 mt-2 font-medium">{option.note}</p>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Costs Overview */}
          {guide.costs && (
            <Card className="border-slate-100 bg-blue-50">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Euro className="h-5 w-5 text-blue-600" />
                  <h3 className="font-semibold text-blue-900">
                    {language === 'pt' ? 'Custos Estimados' : 'Estimated Costs'}
                  </h3>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-blue-700">Theory Test</p>
                    <p className="font-semibold text-blue-900">€{guide.costs.theory_test}</p>
                  </div>
                  <div>
                    <p className="text-xs text-blue-700">Learner Permit</p>
                    <p className="font-semibold text-blue-900">€{guide.costs.learner_permit}</p>
                  </div>
                  <div>
                    <p className="text-xs text-blue-700">EDT (12 aulas)</p>
                    <p className="font-semibold text-blue-900">€{guide.costs.edt_lessons}</p>
                  </div>
                  <div>
                    <p className="text-xs text-blue-700">Practical Test</p>
                    <p className="font-semibold text-blue-900">€{guide.costs.practical_test}</p>
                  </div>
                  <div>
                    <p className="text-xs text-blue-700">Full License</p>
                    <p className="font-semibold text-blue-900">€{guide.costs.full_license}</p>
                  </div>
                  <div className="bg-blue-100 rounded-lg p-2">
                    <p className="text-xs text-blue-700">Total Estimado</p>
                    <p className="font-bold text-blue-900">€{guide.costs.total_estimate}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Timeline */}
          {guide.timeline && (
            <Card className="border-slate-100 bg-purple-50">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Calendar className="h-5 w-5 text-purple-600" />
                  <h3 className="font-semibold text-purple-900">
                    {language === 'pt' ? 'Tempo Estimado' : 'Estimated Timeline'}
                  </h3>
                </div>
                <div className="flex gap-6">
                  <div>
                    <p className="text-xs text-purple-700">{language === 'pt' ? 'Mínimo' : 'Minimum'}</p>
                    <p className="font-semibold text-purple-900">{guide.timeline.minimum}</p>
                  </div>
                  <div>
                    <p className="text-xs text-purple-700">{language === 'pt' ? 'Típico' : 'Typical'}</p>
                    <p className="font-semibold text-purple-900">{guide.timeline.typical}</p>
                  </div>
                </div>
                {guide.timeline.note && (
                  <p className="text-xs text-purple-700 mt-3">{guide.timeline.note}</p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Steps */}
          <div className="space-y-4">
            <h2 className="font-serif text-xl font-semibold text-slate-900">
              {language === 'pt' ? 'Passo a Passo Completo' : 'Complete Step by Step'}
            </h2>
            {guide.steps.map((step, index) => (
              <Card key={index} className="border-slate-100" data-testid={`step-${index}`}>
                <CardContent className="p-6">
                  <div className="flex gap-4">
                    <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="font-bold text-emerald-700">{step.step}</span>
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-slate-900 mb-2">
                        {language === 'pt' ? step.title : step.title_en}
                      </h3>
                      <p className="text-slate-600 text-sm mb-3">
                        {language === 'pt' ? step.description : step.description_en}
                      </p>
                      
                      {step.sub_steps && (
                        <ul className="space-y-1 mb-3">
                          {step.sub_steps.map((sub, j) => (
                            <li key={j} className="flex items-start gap-2 text-sm text-slate-600">
                              <CheckCircle className="h-4 w-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                              {sub}
                            </li>
                          ))}
                        </ul>
                      )}

                      {step.details && (
                        <div className="bg-slate-50 rounded-lg p-3 mb-3">
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div><span className="text-slate-500">Aulas:</span> {step.details.lessons}</div>
                            <div><span className="text-slate-500">Duração:</span> {step.details.duration}</div>
                            <div><span className="text-slate-500">Custo:</span> {step.details.cost_range}</div>
                            <div><span className="text-slate-500">Total:</span> {step.details.total_estimate}</div>
                          </div>
                        </div>
                      )}

                      {step.rules && (
                        <ul className="space-y-1 mb-3">
                          {step.rules.map((rule, j) => (
                            <li key={j} className="flex items-start gap-2 text-sm text-slate-600">
                              <span className="text-amber-600">•</span>
                              {rule}
                            </li>
                          ))}
                        </ul>
                      )}
                      
                      {step.documents && (
                        <div className="mt-3">
                          <p className="text-xs text-slate-500 mb-2">
                            {language === 'pt' ? 'Documentos necessários:' : 'Required documents:'}
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {step.documents.map((doc, i) => (
                              <Badge key={i} variant="secondary" className="text-xs">
                                <FileText className="h-3 w-3 mr-1" />
                                {doc}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {step.cost && (
                        <p className="text-sm text-emerald-700 font-medium mt-2">
                          {language === 'pt' ? 'Custo:' : 'Cost:'} €{step.cost}
                        </p>
                      )}
                      
                      {step.link && (
                        <a 
                          href={step.link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 mt-3 text-sm text-emerald-700 hover:text-emerald-800"
                        >
                          <ExternalLink className="h-4 w-4" />
                          {language === 'pt' ? 'Acessar site' : 'Access website'}
                        </a>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Tips */}
          <Card className="border-slate-100 bg-amber-50">
            <CardContent className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <Lightbulb className="h-5 w-5 text-amber-600" />
                <h3 className="font-semibold text-amber-900">
                  {language === 'pt' ? 'Dicas Importantes' : 'Important Tips'}
                </h3>
              </div>
              <ul className="space-y-2">
                {guide.tips.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-amber-800">
                    <CheckCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                    {tip}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {/* Useful Links */}
          <div>
            <h2 className="font-serif text-xl font-semibold text-slate-900 mb-4">
              {language === 'pt' ? 'Links Úteis' : 'Useful Links'}
            </h2>
            <div className="flex flex-wrap gap-3">
              {guide.useful_links.map((link, i) => (
                <a
                  key={i}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm text-slate-700 hover:border-emerald-300 hover:text-emerald-700 transition-colors"
                >
                  <LinkIcon className="h-4 w-4" />
                  {link.name}
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </GuideLayout>
  );
};