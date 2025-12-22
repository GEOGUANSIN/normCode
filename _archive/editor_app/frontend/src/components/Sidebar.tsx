import React from 'react';
import { SidebarMode } from '../state';
import './Sidebar.css';

interface SidebarProps {
  mode: SidebarMode;
  onModeChange: (mode: SidebarMode) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ mode, onModeChange }) => {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1 className="sidebar-title">Normcode</h1>
        <p className="sidebar-subtitle">Editor</p>
      </div>
      
      <nav className="sidebar-nav">
        <button
          className={`sidebar-nav-item ${mode === 'concepts' ? 'active' : ''}`}
          onClick={() => onModeChange('concepts')}
        >
          <span className="sidebar-nav-icon">📝</span>
          <span className="sidebar-nav-label">Concepts</span>
        </button>
        
        <button
          className={`sidebar-nav-item ${mode === 'inferences' ? 'active' : ''}`}
          onClick={() => onModeChange('inferences')}
        >
          <span className="sidebar-nav-icon">🔄</span>
          <span className="sidebar-nav-label">Inferences</span>
        </button>
        
        <button
          className={`sidebar-nav-item ${mode === 'repositories' ? 'active' : ''}`}
          onClick={() => onModeChange('repositories')}
        >
          <span className="sidebar-nav-icon">📦</span>
          <span className="sidebar-nav-label">Repositories</span>
        </button>
      </nav>

      <div className="sidebar-footer">
        <p className="sidebar-footer-text">
          {mode === 'concepts' && 'Manage global concepts'}
          {mode === 'inferences' && 'Manage global inferences'}
          {mode === 'repositories' && 'Configure repositories'}
        </p>
      </div>
    </div>
  );
};

export default Sidebar;
