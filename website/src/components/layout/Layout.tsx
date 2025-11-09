import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Layout.css';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <Link to="/" className="logo">
            <span className="logo-icon">⚛️</span>
            <span className="logo-text">PsylensAI</span>
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
                  Home
                </Link>
              </li>
              <li>
                <Link 
                  to="/normcode" 
                  className={isActive('/normcode') ? 'active' : ''}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  NormCode
                </Link>
              </li>
              <li>
                <Link 
                  to="/docs" 
                  className={location.pathname.startsWith('/docs') ? 'active' : ''}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Documentation
                </Link>
              </li>
              <li>
                <Link 
                  to="/demo" 
                  className={isActive('/demo') ? 'active' : ''}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Demo
                </Link>
              </li>
              <li>
                <Link 
                  to="/about" 
                  className={isActive('/about') ? 'active' : ''}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  About
                </Link>
              </li>
              <li>
                <Link 
                  to="/blog" 
                  className={isActive('/blog') ? 'active' : ''}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Blog
                </Link>
              </li>
              <li>
                <Link 
                  to="/contact" 
                  className={`contact-link ${isActive('/contact') ? 'active' : ''}`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Contact
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </header>
      <main className="main-content">
        {children}
      </main>
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-section">
            <h3>PsylensAI</h3>
            <p>Building transparent and controllable AI through NormCode</p>
          </div>
          <div className="footer-section">
            <h4>Product</h4>
            <ul>
              <li><Link to="/normcode">NormCode</Link></li>
              <li><Link to="/docs">Documentation</Link></li>
              <li><Link to="/demo">Demo</Link></li>
            </ul>
          </div>
          <div className="footer-section">
            <h4>Company</h4>
            <ul>
              <li><Link to="/about">About</Link></li>
              <li><Link to="/blog">Blog</Link></li>
              <li><Link to="/contact">Contact</Link></li>
            </ul>
          </div>
          <div className="footer-section">
            <h4>Connect</h4>
            <p className="footer-social">
              Building the future of explainable AI
            </p>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; 2025 PsylensAI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
