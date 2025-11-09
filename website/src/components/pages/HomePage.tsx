import React from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css';

const HomePage: React.FC = () => {
  return (
    <div className="home-page">
      <section className="hero">
        <h1>Advancing AI Reasoning</h1>
        <p>PsylensAI is dedicated to developing transparent and controllable AI through our core technology, NormCode.</p>
        <div className="cta-buttons">
          <Link to="/normcode" className="btn btn-primary">Learn about NormCode</Link>
          <Link to="/demo" className="btn btn-secondary">See the Demo</Link>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
