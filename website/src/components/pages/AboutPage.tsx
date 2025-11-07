import React from 'react';
import './AboutPage.css';

const AboutPage: React.FC = () => {
  return (
    <div className="about-page">
      <section>
        <h2>Our Mission</h2>
        <p>Our mission at PsylensAI is to create a future where AI is not only intelligent but also understandable, controllable, and aligned with human values. We believe that the key to safe and beneficial AI is transparency in its reasoning processes.</p>
      </section>
      <section>
        <h2>The Team</h2>
        <p>PsylensAI was founded by a passionate group of researchers and engineers with a shared vision for the future of artificial intelligence. We are experts in AI, cognitive science, and software development, and we are dedicated to solving the complex challenges of AI alignment.</p>
      </section>
    </div>
  );
};

export default AboutPage;
