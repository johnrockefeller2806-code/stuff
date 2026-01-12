import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';
import { MapPin, Mail, Phone } from 'lucide-react';

const LOGO_URL = "https://customer-assets.emergentagent.com/job_dublin-study/artifacts/o9gnc0xi_WhatsApp%20Image%202026-01-11%20at%2023.59.07.jpeg";

export const Footer = () => {
  const { t, language } = useLanguage();

  return (
    <footer className="bg-emerald-950 text-white" data-testid="footer">
      <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-24 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          {/* Brand */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <img 
                src={LOGO_URL} 
                alt="STUFF Intercâmbio" 
                className="h-12 w-auto object-contain bg-white rounded-lg p-1"
              />
            </div>
            <p className="text-emerald-200 text-sm leading-relaxed">
              {language === 'pt' 
                ? 'Conectando estudantes brasileiros às melhores escolas de Dublin. Sem intermediários, direto com a escola.'
                : 'Connecting Brazilian students to the best schools in Dublin. No middlemen, direct with the school.'}
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-semibold mb-4">Links Rápidos</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/schools" className="text-emerald-200 hover:text-white text-sm transition-colors">
                  {t('nav_schools')}
                </Link>
              </li>
              <li>
                <Link to="/transport" className="text-emerald-200 hover:text-white text-sm transition-colors">
                  {t('nav_transport')}
                </Link>
              </li>
              <li>
                <Link to="/services" className="text-emerald-200 hover:text-white text-sm transition-colors">
                  {t('nav_services')}
                </Link>
              </li>
              <li>
                <Link to="/duvidas" className="text-emerald-200 hover:text-white text-sm transition-colors">
                  STUFF Dúvidas
                </Link>
              </li>
            </ul>
          </div>

          {/* Services */}
          <div>
            <h4 className="font-semibold mb-4">Serviços</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/services/pps" className="text-emerald-200 hover:text-white text-sm transition-colors">
                  PPS Number
                </Link>
              </li>
              <li>
                <Link to="/services/gnib" className="text-emerald-200 hover:text-white text-sm transition-colors">
                  GNIB/IRP
                </Link>
              </li>
              <li>
                <Link to="/services/passport" className="text-emerald-200 hover:text-white text-sm transition-colors">
                  Passaporte
                </Link>
              </li>
              <li>
                <Link to="/services/driving-license" className="text-emerald-200 hover:text-white text-sm transition-colors">
                  Carteira de Motorista
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-semibold mb-4">{t('footer_contact')}</h4>
            <ul className="space-y-3">
              <li className="flex items-center gap-2 text-emerald-200 text-sm">
                <MapPin className="h-4 w-4" />
                Dublin, Ireland
              </li>
              <li className="flex items-center gap-2 text-emerald-200 text-sm">
                <Mail className="h-4 w-4" />
                contato@stuffintercambio.com
              </li>
              <li className="flex items-center gap-2 text-emerald-200 text-sm">
                <Phone className="h-4 w-4" />
                +353 1 234 5678
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-emerald-800 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-emerald-300 text-sm">
            © 2025 STUFF Intercâmbio. {t('footer_rights')}.
          </p>
          <div className="flex gap-6">
            <Link to="/terms" className="text-emerald-300 hover:text-white text-sm transition-colors">
              {t('footer_terms')}
            </Link>
            <Link to="/privacy" className="text-emerald-300 hover:text-white text-sm transition-colors">
              {t('footer_privacy')}
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
};
