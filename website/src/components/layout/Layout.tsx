import React from 'react';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div>
      <header>
        <nav>
          <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/about">About</a></li>
            <li><a href="/normcode">NormCode</a></li>
            <li><a href="/docs">Documentation</a></li>
            <li><a href="/demo">Demo</a></li>
            <li><a href="/blog">Blog</a></li>
            <li><a href="/contact">Contact</a></li>
          </ul>
        </nav>
      </header>
      <main>
        {children}
      </main>
    </div>
  );
};

export default Layout;
