import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useLanguage } from '../../contexts/LanguageContext';
import LanguageSwitcher from '../LanguageSwitcher';
import logo from '../../assets/logo.png';
import './Layout.css';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const { t } = useLanguage();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <Link to="/" className="logo">
            <img src={logo} alt="PsylensAI Logo" className="logo-image" />
            <span className="logo-text">{t('company.name')}</span>
          </Link>
          
          <button 
            className="mobile-menu-toggle"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            <span></span>
            <span></span>
            <span></span>
          </button>

          <nav className={`nav ${mobileMenuOpen ? 'nav-open' : ''}`}>
            <ul>
              <li>
                <Link 
                  to="/" 
                  className={isActive('/') ? 'active' : ''}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {t('nav.home')}
                </Link>
              </li>
              <li>
                <Link 
                  to="/normcode" 
                  className={isActive('/normcode') ? 'active' : ''}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {t('nav.normcode')}
                </Link>
              </li>
              <li>
                <Link 
                  to="/docs" 
                  className={location.pathname.startsWith('/docs') ? 'active' : ''}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {t('nav.documentation')}
                </Link>
              </li>
              <li>
                <Link 
                  to="/demo" 
                  className={isActive('/demo') ? 'active' : ''}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {t('nav.demo')}
                </Link>
              </li>
              <li>
                <Link 
                  to="/about" 
                  className={isActive('/about') ? 'active' : ''}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {t('nav.about')}
                </Link>
              </li>
              <li>
                <Link 
                  to="/blog" 
                  className={isActive('/blog') ? 'active' : ''}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {t('nav.blog')}
                </Link>
              </li>
              <li>
                <Link 
                  to="/contact" 
                  className={`contact-link ${isActive('/contact') ? 'active' : ''}`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {t('nav.contact')}
                </Link>
              </li>
            </ul>
            <LanguageSwitcher />
          </nav>
        </div>
      </header>
      <main className="main-content">
        {children}
      </main>
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-section">
            <h3>{t('company.name')}</h3>
            <p>{t('footer.tagline')}</p>
          </div>
          <div className="footer-section">
            <h4>{t('footer.product')}</h4>
            <ul>
              <li><Link to="/normcode">{t('nav.normcode')}</Link></li>
              <li><Link to="/docs">{t('nav.documentation')}</Link></li>
              <li><Link to="/demo">{t('nav.demo')}</Link></li>
            </ul>
          </div>
          <div className="footer-section">
            <h4>{t('footer.company')}</h4>
            <ul>
              <li><Link to="/about">{t('nav.about')}</Link></li>
              <li><Link to="/blog">{t('nav.blog')}</Link></li>
              <li><Link to="/contact">{t('nav.contact')}</Link></li>
            </ul>
          </div>
          <div className="footer-section">
            <h4>{t('footer.connect')}</h4>
            <p className="footer-social">
              {t('footer.connect.desc')}
            </p>
          </div>
        </div>
        <div className="footer-bottom">
          <p>{t('footer.copyright')}</p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
