/**
 * Project Tabs Component
 * Displays open project tabs for multi-project support
 * Includes both local project tabs and remote plan tabs
 */

import { useEffect } from 'react';
import { X, Loader2, Plus, Lock, Sparkles, Globe } from 'lucide-react';
import { useProjectStore } from '../../stores/projectStore';
import { useDeploymentStore } from '../../stores/deploymentStore';
import type { OpenProjectInstance } from '../../types/project';

interface ProjectTabProps {
  tab: OpenProjectInstance;
  isActive: boolean;
  onSwitch: (projectId: string) => void;
  onClose: (projectId: string) => void;
}

function ProjectTab({ tab, isActive, onSwitch, onClose }: ProjectTabProps) {
  // Read-only tabs (compiler) get purple styling
  // Remote tabs get cyan styling (unified with local tabs now)
  const isCompiler = tab.is_read_only && !tab.is_remote;
  const isRemote = tab.is_remote;
  
  // Choose styling based on tab type
  const getTabClasses = () => {
    if (isRemote) {
      // Remote project - cyan theme
      return isActive
        ? 'bg-cyan-50 border-cyan-500 text-slate-800 shadow-sm'
        : 'bg-cyan-100/50 border-transparent text-slate-700 hover:bg-cyan-100 hover:text-slate-800';
    } else if (isCompiler) {
      // Compiler (read-only local) - purple theme
      return isActive
        ? 'bg-purple-50 border-purple-500 text-slate-800 shadow-sm'
        : 'bg-purple-100/50 border-transparent text-slate-700 hover:bg-purple-100 hover:text-slate-800';
    } else {
      // Regular local project - blue theme
      return isActive
        ? 'bg-white border-blue-500 text-slate-800 shadow-sm'
        : 'bg-slate-100 border-transparent text-slate-600 hover:bg-slate-200 hover:text-slate-800';
    }
  };
  
  return (
    <div
      className={`group flex items-center gap-2 px-3 py-1.5 rounded-t-lg cursor-pointer transition-all border-b-2 ${getTabClasses()}`}
      onClick={() => onSwitch(tab.id)}
    >
      {/* Icon based on tab type */}
      {isRemote ? (
        <Globe size={14} className="text-cyan-500" title={`Remote: ${tab.server_name || 'Unknown Server'}`} />
      ) : isCompiler ? (
        <Sparkles size={14} className="text-purple-500" />
      ) : (
        <div className="flex items-center gap-1.5">
          {tab.is_loaded ? (
            <span className="w-2 h-2 bg-green-500 rounded-full" title="Loaded" />
          ) : tab.repositories_exist ? (
            <span className="w-2 h-2 bg-yellow-500 rounded-full" title="Not loaded" />
          ) : (
            <span className="w-2 h-2 bg-red-500 rounded-full" title="Missing files" />
          )}
        </div>
      )}
      
      {/* Tab name */}
      <span className="text-sm font-medium truncate max-w-[120px]" title={isRemote ? `${tab.name} (${tab.server_name})` : tab.name}>
        {tab.name}
      </span>
      
      {/* Close button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onClose(tab.id);
        }}
        className={`p-0.5 rounded transition-colors ${
          isRemote
            ? 'hover:bg-cyan-200/50'
            : isCompiler
              ? 'hover:bg-purple-200/50'
              : 'hover:bg-slate-300/50'
        } ${isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
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
  
  const { loadedRemoteGraph } = useDeploymentStore();

  // Fetch open tabs on mount
  useEffect(() => {
    fetchOpenTabs();
  }, [fetchOpenTabs]);

  // Total tab count (unified - includes both local and remote)
  const totalTabs = openTabs.length;
  
  // Don't show if no tabs or only one tab
  if (totalTabs <= 1) {
    return null;
  }

  // Sort tabs: remote first, then read-only (pinned), then regular
  const sortedTabs = [...openTabs].sort((a, b) => {
    // Remote tabs first
    if (a.is_remote && !b.is_remote) return -1;
    if (!a.is_remote && b.is_remote) return 1;
    // Then read-only tabs
    if (a.is_read_only && !b.is_read_only) return -1;
    if (!a.is_read_only && b.is_read_only) return 1;
    return 0;
  });
  
  // Handle switching tabs
  const handleSwitch = async (tabId: string) => {
    await switchTab(tabId);
  };
  
  // Handle closing tab
  const handleClose = async (tabId: string) => {
    // If this is a remote tab and its graph is loaded, clear it
    const tab = openTabs.find(t => t.id === tabId);
    if (tab?.is_remote && loadedRemoteGraph) {
      useDeploymentStore.getState().set({ loadedRemoteGraph: null });
    }
    await closeTab(tabId);
  };

  return (
    <div className="bg-slate-200 border-b border-slate-300 px-2 flex items-end gap-0.5">
      {/* All project tabs (unified local + remote) */}
      {sortedTabs.map((tab) => (
        <ProjectTab
          key={tab.id}
          tab={tab}
          isActive={tab.id === activeTabId}
          onSwitch={handleSwitch}
          onClose={handleClose}
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

  // Sort tabs: read-only (pinned) tabs first
  const sortedTabs = [...openTabs].sort((a, b) => {
    if (a.is_read_only && !b.is_read_only) return -1;
    if (!a.is_read_only && b.is_read_only) return 1;
    return 0;
  });

  return (
    <div className="flex items-center gap-1 ml-2">
      {sortedTabs.map((tab) => (
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
            <span title="Read-only">
              <Lock size={10} className="text-slate-400" />
            </span>
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

