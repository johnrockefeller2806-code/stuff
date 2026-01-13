import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { Menu, X, Globe, User, LogOut, LayoutDashboard, Building2, Shield, HelpCircle, MessageCircle, Camera } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';

const LOGO_URL = "https://customer-assets.emergentagent.com/job_dublin-study/artifacts/o9gnc0xi_WhatsApp%20Image%202026-01-11%20at%2023.59.07.jpeg";

export const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { user, isAuthenticated, isAdmin, isSchool, logout } = useAuth();
  const { language, toggleLanguage, t } = useLanguage();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const getDashboardLink = () => {
    if (isAdmin) return '/admin';
    if (isSchool) return '/school';
    return '/dashboard';
  };

  const getDashboardLabel = () => {
    if (isAdmin) return language === 'pt' ? 'Admin' : 'Admin';
    if (isSchool) return language === 'pt' ? 'Minha Escola' : 'My School';
    return t('nav_dashboard');
  };

  const getInitials = (name) => {
    return name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || '?';
  };

  const navLinks = [
    { href: '/schools', label: t('nav_schools') },
    { href: '/transport', label: t('nav_transport') },
    { href: '/services', label: t('nav_services') },
    { href: '/chat', label: 'STUFF Online', icon: MessageCircle },
    { href: '/duvidas', label: 'STUFF Dúvidas' },
  ];

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-xl bg-white/80 border-b border-slate-100" data-testid="navbar">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2" data-testid="nav-logo">
              <img 
                src={LOGO_URL} 
                alt="STUFF Intercâmbio" 
                className="h-10 w-auto object-contain"
              />
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-emerald-900 hover:bg-emerald-50 rounded-lg transition-colors"
                data-testid={`nav-link-${link.href.slice(1)}`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-3">
            {/* Language Toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleLanguage}
              className="gap-2"
              data-testid="language-toggle"
            >
              <Globe className="h-4 w-4" />
              {language.toUpperCase()}
            </Button>

            {isAuthenticated ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="gap-2 pl-1" data-testid="user-menu-trigger">
                    <Avatar className="h-7 w-7">
                      <AvatarImage src={user?.avatar} alt={user?.name} />
                      <AvatarFallback className={`text-xs ${isAdmin ? 'bg-amber-100 text-amber-700' : isSchool ? 'bg-purple-100 text-purple-700' : 'bg-emerald-100 text-emerald-700'}`}>
                        {getInitials(user?.name)}
                      </AvatarFallback>
                    </Avatar>
                    {user?.name?.split(' ')[0]}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <DropdownMenuItem onClick={() => navigate('/profile')} data-testid="nav-profile">
                    <Camera className="h-4 w-4 mr-2" />
                    {language === 'pt' ? 'Meu Perfil' : 'My Profile'}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate(getDashboardLink())} data-testid="nav-dashboard">
                    <LayoutDashboard className="h-4 w-4 mr-2" />
                    {getDashboardLabel()}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} data-testid="nav-logout">
                    <LogOut className="h-4 w-4 mr-2" />
                    {t('nav_logout')}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost" size="sm" data-testid="nav-login">
                    {t('nav_login')}
                  </Button>
                </Link>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button size="sm" className="bg-emerald-900 hover:bg-emerald-800" data-testid="nav-register">
                      {t('nav_register')}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    <DropdownMenuItem onClick={() => navigate('/register')}>
                      <User className="h-4 w-4 mr-2" />
                      {language === 'pt' ? 'Como Estudante' : 'As Student'}
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => navigate('/register-school')}>
                      <Building2 className="h-4 w-4 mr-2" />
                      {language === 'pt' ? 'Como Escola' : 'As School'}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleLanguage}
              data-testid="mobile-language-toggle"
            >
              <Globe className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsOpen(!isOpen)}
              data-testid="mobile-menu-button"
            >
              {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden py-4 border-t border-slate-100 animate-fade-in" data-testid="mobile-menu">
            <div className="flex flex-col gap-2">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  to={link.href}
                  className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-emerald-900 hover:bg-emerald-50 rounded-lg"
                  onClick={() => setIsOpen(false)}
                >
                  {link.label}
                </Link>
              ))}
              <div className="border-t border-slate-100 pt-2 mt-2">
                {isAuthenticated ? (
                  <>
                    <Link
                      to={getDashboardLink()}
                      className="block px-4 py-2 text-sm font-medium text-slate-600 hover:text-emerald-900"
                      onClick={() => setIsOpen(false)}
                    >
                      {getDashboardLabel()}
                    </Link>
                    <button
                      onClick={() => { handleLogout(); setIsOpen(false); }}
                      className="block w-full text-left px-4 py-2 text-sm font-medium text-slate-600 hover:text-emerald-900"
                    >
                      {t('nav_logout')}
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      to="/login"
                      className="block px-4 py-2 text-sm font-medium text-slate-600 hover:text-emerald-900"
                      onClick={() => setIsOpen(false)}
                    >
                      {t('nav_login')}
                    </Link>
                    <Link
                      to="/register"
                      className="block px-4 py-2 text-sm font-medium text-emerald-900"
                      onClick={() => setIsOpen(false)}
                    >
                      {language === 'pt' ? 'Cadastrar Estudante' : 'Register Student'}
                    </Link>
                    <Link
                      to="/register-school"
                      className="block px-4 py-2 text-sm font-medium text-emerald-700"
                      onClick={() => setIsOpen(false)}
                    >
                      {language === 'pt' ? 'Cadastrar Escola' : 'Register School'}
                    </Link>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};
