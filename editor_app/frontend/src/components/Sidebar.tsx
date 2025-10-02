import React from 'react';

interface SidebarProps {
  repositorySets: string[];
  selectedRepo: string | null;
  onRepoSelect: (repoName: string) => void;
  onNewRepo: () => void;
  onLoadRepo: () => void;
  onSaveRepo: () => void;
  onDeleteRepo: () => void;
  onRunRepo: () => void;
  isRunning: boolean;
  disabled: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  repositorySets,
  selectedRepo,
  onRepoSelect,
  onNewRepo,
  onLoadRepo,
  onSaveRepo,
  onDeleteRepo,
  onRunRepo,
  isRunning,
  disabled
}) => {
  return (
    <div className="sidebar">
      <h2>Repository Sets</h2>
      <select
        className="repo-selector"
        size={10}
        value={selectedRepo || ''}
        onChange={(e) => onRepoSelect(e.target.value)}
        disabled={disabled}
      >
        {repositorySets.map((name) => (
          <option key={name} value={name}>
            {name}
          </option>
        ))}
      </select>
      
      <div className="controls">
        <button onClick={onNewRepo} disabled={disabled}>
          New
        </button>
        <button onClick={onLoadRepo} disabled={disabled || !selectedRepo}>
          Load
        </button>
        <button onClick={onSaveRepo} disabled={disabled} className="success">
          Save
        </button>
        <button 
          onClick={onDeleteRepo} 
          disabled={disabled || !selectedRepo}
          className="danger"
        >
          Delete
        </button>
        <button 
          onClick={onRunRepo} 
          disabled={disabled || (!selectedRepo && !isRunning)}
          className={isRunning ? 'danger' : 'success'}
        >
          {isRunning ? 'Stop' : 'Run'}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
