import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import './DocsLayout.css';

const DocsLayout: React.FC = () => {
  return (
    <div className="docs-layout">
      <aside className="docs-sidebar">
        <nav>
          <ul>
            <li><NavLink to="/docs/getting-started">Getting Started</NavLink></li>
            <li><NavLink to="/docs/concepts">Core Concepts</NavLink></li>
            <li><NavLink to="/docs/operators">Operators</NavLink></li>
          </ul>
        </nav>
      </aside>
      <main className="docs-content">
        <Outlet />
      </main>
    </div>
  );
};

export default DocsLayout;
