/**
 * Project Tabs Component
 * Displays open project tabs for multi-project support
 */

import { useEffect } from 'react';
import { X, FolderOpen, Loader2, Plus, Lock } from 'lucide-react';
import { useProjectStore } from '../../stores/projectStore';
import type { OpenProjectInstance } from '../../types/project';

interface ProjectTabProps {
  tab: OpenProjectInstance;
  isActive: boolean;
  onSwitch: (projectId: string) => void;
  onClose: (projectId: string) => void;
}

function ProjectTab({ tab, isActive, onSwitch, onClose }: ProjectTabProps) {
  return (
    <div
      className={`group flex items-center gap-2 px-3 py-1.5 rounded-t-lg cursor-pointer transition-all border-b-2 ${
        isActive
          ? 'bg-white border-blue-500 text-slate-800 shadow-sm'
          : 'bg-slate-100 border-transparent text-slate-600 hover:bg-slate-200 hover:text-slate-800'
      }`}
      onClick={() => onSwitch(tab.id)}
    >
      {/* Status indicator */}
      <div className="flex items-center gap-1.5">
        {tab.is_loaded ? (
          <span className="w-2 h-2 bg-green-500 rounded-full" title="Loaded" />
        ) : tab.repositories_exist ? (
          <span className="w-2 h-2 bg-yellow-500 rounded-full" title="Not loaded" />
        ) : (
          <span className="w-2 h-2 bg-red-500 rounded-full" title="Missing files" />
        )}
      </div>
      
      {/* Tab name */}
      <span className="text-sm font-medium truncate max-w-[120px]" title={tab.name}>
        {tab.name}
      </span>
      
      {/* Read-only indicator */}
      {tab.is_read_only && (
        <Lock size={12} className="text-slate-400" title="Read-only project" />
      )}
      
      {/* Close button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onClose(tab.id);
        }}
        className={`p-0.5 rounded hover:bg-slate-300/50 transition-colors ${
          isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
        }`}
        title="Close tab"
      >
        <X size={14} />
      </button>
    </div>
  );
}

interface ProjectTabsProps {
  onOpenProjectPanel?: () => void;
}

export function ProjectTabs({ onOpenProjectPanel }: ProjectTabsProps) {
  const {
    openTabs,
    activeTabId,
    isLoading,
    fetchOpenTabs,
    switchTab,
    closeTab,
  } = useProjectStore();

  // Fetch open tabs on mount
  useEffect(() => {
    fetchOpenTabs();
  }, [fetchOpenTabs]);

  // Don't show if no tabs
  if (openTabs.length === 0) {
    return null;
  }

  // Don't show if only one tab (no need for tabs UI)
  if (openTabs.length === 1) {
    return null;
  }

  return (
    <div className="bg-slate-200 border-b border-slate-300 px-2 flex items-end gap-0.5">
      {/* Tabs */}
      {openTabs.map((tab) => (
        <ProjectTab
          key={tab.id}
          tab={tab}
          isActive={tab.id === activeTabId}
          onSwitch={switchTab}
          onClose={closeTab}
        />
      ))}
      
      {/* Add new tab button */}
      {onOpenProjectPanel && (
        <button
          onClick={onOpenProjectPanel}
          disabled={isLoading}
          className="p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-300/50 rounded transition-colors mb-0.5"
          title="Open another project"
        >
          {isLoading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Plus size={16} />
          )}
        </button>
      )}
    </div>
  );
}

/**
 * Compact version of tabs for the header bar
 */
export function ProjectTabsCompact() {
  const {
    openTabs,
    activeTabId,
    switchTab,
    closeTab,
  } = useProjectStore();

  if (openTabs.length <= 1) {
    return null;
  }

  return (
    <div className="flex items-center gap-1 ml-2">
      {openTabs.map((tab) => (
        <div
          key={tab.id}
          onClick={() => switchTab(tab.id)}
          className={`group flex items-center gap-1 px-2 py-0.5 rounded cursor-pointer transition-all text-xs ${
            tab.id === activeTabId
              ? 'bg-blue-100 text-blue-700 font-medium'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          {/* Status dot */}
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              tab.is_loaded
                ? 'bg-green-500'
                : tab.repositories_exist
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`}
          />
          
          {/* Name */}
          <span className="truncate max-w-[80px]" title={tab.name}>
            {tab.name}
          </span>
          
          {/* Read-only indicator */}
          {tab.is_read_only && (
            <Lock size={10} className="text-slate-400" title="Read-only" />
          )}
          
          {/* Close */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              closeTab(tab.id);
            }}
            className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-slate-300/50 rounded transition-all"
          >
            <X size={10} />
          </button>
        </div>
      ))}
    </div>
  );
}

