import React from 'react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../../contexts/LanguageContext';
import './HomePage.css';

const HomePage: React.FC = () => {
  const { t } = useLanguage();

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">{t('hero.title')}</h1>
          <p className="hero-subtitle">
            {t('hero.subtitle')}
          </p>
          <div className="cta-buttons">
            <Link to="/normcode" className="btn btn-primary">{t('hero.cta.primary')}</Link>
            <Link to="/demo" className="btn btn-secondary">{t('hero.cta.secondary')}</Link>
          </div>
        </div>
        <div className="hero-visual">
          <div className="floating-card">
            <div className="code-snippet">
              <div className="code-line">{t('code.norm')} <span className="keyword">{t('code.transparency')}</span>:</div>
              <div className="code-line">  {t('code.reasoning')} = <span className="string">"{t('code.explainable')}"</span></div>
              <div className="code-line">  {t('code.control')} = <span className="string">"{t('code.human_aligned')}"</span></div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <h2 className="section-title">{t('features.title')}</h2>
        <p className="section-subtitle">{t('features.subtitle')}</p>
        
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h3>{t('features.transparent.title')}</h3>
            <p>
              {t('features.transparent.desc')}
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">⚙️</div>
            <h3>{t('features.control.title')}</h3>
            <p>
              {t('features.control.desc')}
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3>{t('features.alignment.title')}</h3>
            <p>
              {t('features.alignment.desc')}
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">🚀</div>
            <h3>{t('features.production.title')}</h3>
            <p>
              {t('features.production.desc')}
            </p>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats">
        <div className="stat-item">
          <div className="stat-number">100%</div>
          <div className="stat-label">{t('stats.traceable')}</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">10x</div>
          <div className="stat-label">{t('stats.faster')}</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">Zero</div>
          <div className="stat-label">{t('stats.blackbox')}</div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works">
        <h2 className="section-title">{t('howitworks.title')}</h2>
        <p className="section-subtitle">{t('howitworks.subtitle')}</p>
        
        <div className="steps">
          <div className="step">
            <div className="step-number">1</div>
            <h3>{t('howitworks.step1.title')}</h3>
            <p>
              {t('howitworks.step1.desc')}
            </p>
          </div>
          
          <div className="step">
            <div className="step-number">2</div>
            <h3>{t('howitworks.step2.title')}</h3>
            <p>
              {t('howitworks.step2.desc')}
            </p>
          </div>
          
          <div className="step">
            <div className="step-number">3</div>
            <h3>{t('howitworks.step3.title')}</h3>
            <p>
              {t('howitworks.step3.desc')}
            </p>
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="use-cases">
        <h2 className="section-title">{t('usecases.title')}</h2>
        <p className="section-subtitle">{t('usecases.subtitle')}</p>
        
        <div className="use-cases-grid">
          <div className="use-case-card">
            <h4>{t('usecases.healthcare.title')}</h4>
            <p>{t('usecases.healthcare.desc')}</p>
          </div>
          <div className="use-case-card">
            <h4>{t('usecases.finance.title')}</h4>
            <p>{t('usecases.finance.desc')}</p>
          </div>
          <div className="use-case-card">
            <h4>{t('usecases.legal.title')}</h4>
            <p>{t('usecases.legal.desc')}</p>
          </div>
          <div className="use-case-card">
            <h4>{t('usecases.research.title')}</h4>
            <p>{t('usecases.research.desc')}</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <h2>{t('cta.title')}</h2>
        <p>{t('cta.subtitle')}</p>
        <div className="cta-buttons-large">
          <Link to="/docs" className="btn btn-primary-large">{t('cta.primary')}</Link>
          <Link to="/contact" className="btn btn-secondary-large">{t('cta.secondary')}</Link>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
