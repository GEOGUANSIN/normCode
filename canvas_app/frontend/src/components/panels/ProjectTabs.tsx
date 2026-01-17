/**
 * Project Tabs Component
 * Displays open project tabs for multi-project support
 * Includes both local project tabs and remote plan tabs
 */

import { useEffect } from 'react';
import { X, Loader2, Plus, Lock, Sparkles, Globe } from 'lucide-react';
import { useProjectStore } from '../../stores/projectStore';
import { useDeploymentStore } from '../../stores/deploymentStore';
import type { OpenProjectInstance, RemoteProjectTab } from '../../types/project';

interface ProjectTabProps {
  tab: OpenProjectInstance;
  isActive: boolean;
  onSwitch: (projectId: string) => void;
  onClose: (projectId: string) => void;
}

function ProjectTab({ tab, isActive, onSwitch, onClose }: ProjectTabProps) {
  // Read-only tabs (compiler) get purple styling
  const isCompiler = tab.is_read_only;
  
  return (
    <div
      className={`group flex items-center gap-2 px-3 py-1.5 rounded-t-lg cursor-pointer transition-all border-b-2 ${
        isCompiler
          ? isActive
            ? 'bg-purple-50 border-purple-500 text-slate-800 shadow-sm'
            : 'bg-purple-100/50 border-transparent text-slate-700 hover:bg-purple-100 hover:text-slate-800'
          : isActive
            ? 'bg-white border-blue-500 text-slate-800 shadow-sm'
            : 'bg-slate-100 border-transparent text-slate-600 hover:bg-slate-200 hover:text-slate-800'
      }`}
      onClick={() => onSwitch(tab.id)}
    >
      {/* Compiler icon for read-only tabs, status indicator for others */}
      {isCompiler ? (
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
      <span className="text-sm font-medium truncate max-w-[120px]" title={tab.name}>
        {tab.name}
      </span>
      
      {/* Close button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onClose(tab.id);
        }}
        className={`p-0.5 rounded transition-colors ${
          isCompiler
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

// Remote project tab component (for plans loaded from deployment servers)
interface RemoteProjectTabProps {
  tab: RemoteProjectTab;
  isActive: boolean;
  onSwitch: (tabId: string) => void;
  onClose: (tabId: string) => void;
}

function RemoteTab({ tab, isActive, onSwitch, onClose }: RemoteProjectTabProps) {
  // Bound tabs (with live updates) get cyan styling, others get violet
  const isBound = tab.is_bound && tab.run_id;
  
  return (
    <div
      className={`group flex items-center gap-2 px-3 py-1.5 rounded-t-lg cursor-pointer transition-all border-b-2 ${
        isBound
          ? isActive
            ? 'bg-cyan-50 border-cyan-500 text-slate-800 shadow-sm'
            : 'bg-cyan-100/50 border-transparent text-slate-700 hover:bg-cyan-100 hover:text-slate-800'
          : isActive
            ? 'bg-violet-50 border-violet-500 text-slate-800 shadow-sm'
            : 'bg-violet-100/50 border-transparent text-slate-700 hover:bg-violet-100 hover:text-slate-800'
      }`}
      onClick={() => onSwitch(tab.id)}
    >
      {/* Icon: Radio for live/bound, Globe for static remote */}
      {isBound ? (
        <div className="relative">
          <Globe size={14} className="text-cyan-600" />
          {/* Live indicator dot */}
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-green-500 rounded-full animate-pulse" title="Live" />
        </div>
      ) : (
        <Globe size={14} className="text-violet-500" />
      )}
      
      {/* Tab name with server indicator */}
      <span className="text-sm font-medium truncate max-w-[120px]" title={`${tab.plan_name} (${tab.server_name})${isBound ? ' - Live' : ''}`}>
        {tab.name}
      </span>
      
      {/* Close button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onClose(tab.id);
        }}
        className={`p-0.5 rounded transition-colors ${isBound ? 'hover:bg-cyan-200/50' : 'hover:bg-violet-200/50'} ${isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
        title="Close remote tab"
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
    remoteProjectTabs,
    activeRemoteTabId,
    isLoading,
    fetchOpenTabs,
    switchToLocalTab,
    switchToRemoteTab,
    closeTab,
    closeRemoteTab,
  } = useProjectStore();
  
  const { clearLoadedRemoteGraph, loadedRemoteGraph } = useDeploymentStore();

  // Fetch open tabs on mount
  useEffect(() => {
    fetchOpenTabs();
  }, [fetchOpenTabs]);

  // Total tab count (local + remote)
  const totalTabs = openTabs.length + remoteProjectTabs.length;
  
  // Don't show if no tabs or only one local tab with no remote tabs
  if (totalTabs === 0) {
    return null;
  }
  if (totalTabs === 1 && remoteProjectTabs.length === 0) {
    return null;
  }

  // Sort local tabs: read-only (pinned) tabs first
  const sortedLocalTabs = [...openTabs].sort((a, b) => {
    if (a.is_read_only && !b.is_read_only) return -1;
    if (!a.is_read_only && b.is_read_only) return 1;
    return 0;
  });
  
  // Handle switching to local tab
  const handleSwitchToLocal = (tabId: string) => {
    // Clear the remote graph if we're switching away from a remote tab
    if (loadedRemoteGraph) {
      useDeploymentStore.getState().set({ loadedRemoteGraph: null });
    }
    switchToLocalTab(tabId);
  };
  
  // Handle closing remote tab
  const handleCloseRemote = (tabId: string) => {
    closeRemoteTab(tabId);
    // If this was the loaded graph, clear it
    if (loadedRemoteGraph && `remote:${loadedRemoteGraph.server_id}:${loadedRemoteGraph.plan_id}` === tabId) {
      useDeploymentStore.getState().set({ loadedRemoteGraph: null });
    }
  };

  return (
    <div className="bg-slate-200 border-b border-slate-300 px-2 flex items-end gap-0.5">
      {/* Local project tabs */}
      {sortedLocalTabs.map((tab) => (
        <ProjectTab
          key={tab.id}
          tab={tab}
          isActive={tab.id === activeTabId && !activeRemoteTabId}
          onSwitch={handleSwitchToLocal}
          onClose={closeTab}
        />
      ))}
      
      {/* Separator between local and remote tabs */}
      {openTabs.length > 0 && remoteProjectTabs.length > 0 && (
        <div className="w-px h-5 bg-slate-400 mx-1 self-center" />
      )}
      
      {/* Remote project tabs */}
      {remoteProjectTabs.map((tab) => (
        <RemoteTab
          key={tab.id}
          tab={tab}
          isActive={tab.id === activeRemoteTabId}
          onSwitch={switchToRemoteTab}
          onClose={handleCloseRemote}
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

