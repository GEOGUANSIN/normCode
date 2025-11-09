import React from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css';

const HomePage: React.FC = () => {
  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">Advancing AI Reasoning with Transparency</h1>
          <p className="hero-subtitle">
            Building the future of explainable AI through NormCode—a revolutionary framework 
            that makes AI reasoning transparent, controllable, and aligned with human values.
          </p>
          <div className="cta-buttons">
            <Link to="/normcode" className="btn btn-primary">Explore NormCode</Link>
            <Link to="/demo" className="btn btn-secondary">Try Live Demo</Link>
          </div>
        </div>
        <div className="hero-visual">
          <div className="floating-card">
            <div className="code-snippet">
              <div className="code-line">norm <span className="keyword">transparency</span>:</div>
              <div className="code-line">  reasoning = <span className="string">"explainable"</span></div>
              <div className="code-line">  control = <span className="string">"human-aligned"</span></div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <h2 className="section-title">Why NormCode?</h2>
        <p className="section-subtitle">A new paradigm for building trustworthy AI systems</p>
        
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🔍</div>
            <h3>Transparent Reasoning</h3>
            <p>
              Every decision is traceable and explainable. Understand exactly how your AI 
              arrives at conclusions with full reasoning transparency.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">⚙️</div>
            <h3>Fine-Grained Control</h3>
            <p>
              Define precise constraints and norms for your AI. Maintain control over 
              reasoning processes and ensure alignment with your values.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3>Normative Alignment</h3>
            <p>
              Built on formal frameworks that ensure AI behavior aligns with specified 
              norms, values, and ethical guidelines.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">🚀</div>
            <h3>Production Ready</h3>
            <p>
              Seamlessly integrate with existing systems. Scale from prototypes to 
              production with enterprise-grade reliability.
            </p>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats">
        <div className="stat-item">
          <div className="stat-number">100%</div>
          <div className="stat-label">Traceable Reasoning</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">10x</div>
          <div className="stat-label">Faster Debugging</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">Zero</div>
          <div className="stat-label">Black Box Operations</div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works">
        <h2 className="section-title">How NormCode Works</h2>
        <p className="section-subtitle">Three simple steps to transparent AI</p>
        
        <div className="steps">
          <div className="step">
            <div className="step-number">1</div>
            <h3>Define Your Norms</h3>
            <p>
              Specify the rules, values, and constraints that should govern your AI's 
              behavior using NormCode's intuitive syntax.
            </p>
          </div>
          
          <div className="step">
            <div className="step-number">2</div>
            <h3>Build Reasoning Chains</h3>
            <p>
              Create explicit inference pathways that show how conclusions are derived 
              from premises, making every step auditable.
            </p>
          </div>
          
          <div className="step">
            <div className="step-number">3</div>
            <h3>Deploy with Confidence</h3>
            <p>
              Run your AI systems knowing every decision can be explained, debugged, 
              and verified against your specified norms.
            </p>
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="use-cases">
        <h2 className="section-title">Trusted by Leading Organizations</h2>
        <p className="section-subtitle">Making AI transparent across industries</p>
        
        <div className="use-cases-grid">
          <div className="use-case-card">
            <h4>Healthcare</h4>
            <p>Explainable diagnostic systems that physicians can trust and verify</p>
          </div>
          <div className="use-case-card">
            <h4>Finance</h4>
            <p>Auditable decision-making for regulatory compliance and risk management</p>
          </div>
          <div className="use-case-card">
            <h4>Legal Tech</h4>
            <p>Transparent reasoning for case analysis and legal research</p>
          </div>
          <div className="use-case-card">
            <h4>Research</h4>
            <p>Reproducible AI experiments with fully documented reasoning paths</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <h2>Ready to Build Transparent AI?</h2>
        <p>Join the future of explainable and controllable artificial intelligence</p>
        <div className="cta-buttons-large">
          <Link to="/docs" className="btn btn-primary-large">Get Started</Link>
          <Link to="/contact" className="btn btn-secondary-large">Talk to Us</Link>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
